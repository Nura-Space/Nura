"""Context manager with turn-based token compression."""
import time
from typing import List, Optional, Callable, Any, Awaitable

from loguru import logger

from nura.core.schema import Message, Role
from nura.context.config import ContextConfig


class ContextManager:
    """
    Manages conversation context with turn-based compression.

    Features:
    - Automatic token tracking using tiktoken
    - Turn-based message grouping (user message + assistant responses)
    - Context compression via LLM summarization when threshold reached
    - Keeps recent N turns, compresses older ones

    A "turn" is defined as:
    - One user message + the assistant's response(s) until the next user message
    """

    def __init__(self, config: Optional[ContextConfig] = None):
        self.config = config or ContextConfig()
        self._messages: List[Message] = []
        self._summary: Optional[str] = None
        self._token_count: int = 0
        self._last_compress_time: float = 0
        self._compress_callbacks: List[Callable[[], Any]] = []
        self._turn_boundaries: List[int] = []  # Indices where turns start

        # Initialize tokenizer for accurate token counting
        self._tokenizer: Optional[Any] = None  # tiktoken encoding
        try:
            import tiktoken
            try:
                self._tokenizer = tiktoken.encoding_for_model("gpt-4")
            except KeyError:
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            # Fallback to simple estimation
            logger.warning("tiktoken not available, using token estimation")

    def _estimate_tokens_simple(self, text: str) -> int:
        """Fallback token estimation: ~1 token per 4 characters"""
        return len(text) // 4 if text else 0

    def _count_tokens(self, text: str) -> int:
        """Count tokens accurately using tiktoken"""
        if not text:
            return 0
        if self._tokenizer:
            return len(self._tokenizer.encode(text))
        return self._estimate_tokens_simple(text)

    def _count_message_tokens(self, message: Message) -> int:
        """Count tokens for a single message"""
        tokens = 4  # Base tokens per message

        # Role tokens
        tokens += self._count_tokens(message.role)

        # Content tokens
        if message.content:
            tokens += self._count_tokens(message.content)

        # Tool calls tokens
        if message.tool_calls:
            for tc in message.tool_calls:
                tokens += self._count_tokens(tc.function.name)
                tokens += self._count_tokens(tc.function.arguments)

        # Name and tool_call_id
        if message.name:
            tokens += self._count_tokens(message.name)
        if message.tool_call_id:
            tokens += self._count_tokens(message.tool_call_id)

        return tokens

    def add_message(self, message: Message) -> None:
        """Add a message to the context"""
        self._messages.append(message)

        # Check if this starts a new turn (user message)
        if message.role == Role.USER:
            self._turn_boundaries.append(len(self._messages) - 1)

        self._update_token_count()

    def get_messages(self) -> List[Message]:
        """Get all messages in current context"""
        return self._messages.copy()

    def _get_turns(self) -> List[List[Message]]:
        """Split messages into conversation turns.

        A turn starts with a user message and includes all subsequent
        assistant messages until the next user message.
        """
        if not self._messages:
            return []

        turns = []
        current_turn = []

        for msg in self._messages:
            current_turn.append(msg)
            # Each user message starts a new turn
            if msg.role == Role.USER and current_turn[:-1]:
                turns.append(current_turn[:-1])
                current_turn = [msg]

        # Add the last turn
        if current_turn:
            turns.append(current_turn)

        return turns

    def _get_messages_for_compression(self) -> List[Message]:
        """Get messages that need to be compressed (before the keep_turns)."""
        turns = self._get_turns()
        keep_turns = self.config.keep_turns

        if len(turns) <= keep_turns:
            return []

        # Return all messages from turn 0 to turn (keep_turns - 1)
        # i.e., everything before the keep_turns
        compress_count = sum(len(turns[i]) for i in range(len(turns) - keep_turns))
        return self._messages[:compress_count]

    def _get_keep_messages(self) -> List[Message]:
        """Get messages to keep (recent N turns)."""
        turns = self._get_turns()
        keep_turns = self.config.keep_turns

        if len(turns) <= keep_turns:
            return self._messages.copy()

        # Keep the last N turns
        keep_count = sum(len(turns[i]) for i in range(len(turns) - keep_turns, len(turns)))
        return self._messages[-keep_count:]

    def get_messages_for_llm(self) -> List[dict]:
        """Get messages formatted for LLM API."""
        messages = []

        # Add summary if exists (from compressed older turns)
        if self._summary:
            messages.append({
                "role": "system",
                "content": f"Previous conversation summary:\n{self._summary}"
            })

        # Add messages to keep (recent N turns)
        keep_messages = self._get_keep_messages()
        for msg in keep_messages:
            msg_dict = msg.to_dict()
            messages.append(msg_dict)

        return messages

    def _update_token_count(self) -> None:
        """Update estimated token count"""
        total = 0
        for msg in self._messages:
            total += self._count_message_tokens(msg)
        self._token_count = total

    @property
    def token_count(self) -> int:
        """Get estimated token count"""
        return self._token_count

    @property
    def compress_threshold_tokens(self) -> int:
        """Get the token count threshold for compression"""
        return self.config.compress_tokens

    @property
    def needs_compression(self) -> bool:
        """Check if context needs compression"""
        return self._token_count >= self.compress_threshold_tokens

    @property
    def turn_count(self) -> int:
        """Get the number of conversation turns"""
        return len(self._get_turns())

    async def compress(self, summarizer: Optional[Callable[[List[Message]], Awaitable[str]]] = None) -> bool:
        """
        Compress context by summarizing older turns.

        Args:
            summarizer: Optional async function to summarize messages

        Returns:
            True if compression was successful
        """
        # Check if there's anything to compress
        compress_messages = self._get_messages_for_compression()
        if not compress_messages:
            logger.info("No older turns to compress")
            return False

        # Don't compress too frequently
        if time.time() - self._last_compress_time < self.config.compress_cooldown:
            logger.debug("Skipping compression - too soon")
            return False

        logger.info(f"Compressing context: {len(self._messages)} messages, {self.turn_count} turns, ~{self._token_count} tokens")

        if summarizer:
            try:
                self._summary = await summarizer(compress_messages)
            except Exception as e:
                logger.error(f"Summarization failed: {e}")
                # Fallback to simple truncation
                self._summary = f"[Summary of {len(compress_messages)} messages from earlier conversation]"
        else:
            # Simple fallback
            self._summary = f"[Summary of {len(compress_messages)} messages from earlier conversation]"

        # Keep only recent N turns
        self._messages = self._get_keep_messages()

        # Reset turn boundaries
        self._turn_boundaries = [0]  # Start from 0

        self._update_token_count()
        self._last_compress_time = time.time()

        # Notify callbacks
        for callback in self._compress_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Compress callback error: {e}")

        logger.info(f"Compression complete: {len(self._messages)} messages, {self.turn_count} turns, ~{self._token_count} tokens")
        return True

    def register_compress_callback(self, callback: Callable[[], Any]) -> None:
        """Register a callback to be called after compression"""
        self._compress_callbacks.append(callback)

    def clear(self) -> None:
        """Clear all context"""
        self._messages.clear()
        self._summary = None
        self._token_count = 0
        self._turn_boundaries.clear()
