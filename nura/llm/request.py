"""Request builder for LLM requests - handles common logic."""

import time
from typing import Any, Callable, Dict, List, Optional, Union

from nura.config import get_config
from nura.core.schema import Message

from nura.llm.adapters import ArkMessageAdapter
from nura.llm.constants import REASONING_MODELS
from nura.llm.message import format_messages as fmt_msgs


class RequestBuilder:
    """Handles common LLM request logic."""

    def __init__(
        self,
        token_counter: Any,
        check_token_limit: Callable[[int], bool],
        get_limit_error_message: Callable[[int], str],
    ):
        """Initialize RequestBuilder.

        Args:
            token_counter: TokenCounter instance for counting tokens
            check_token_limit: Function to check if token limit is exceeded
            get_limit_error_message: Function to generate error message
        """
        self.token_counter = token_counter
        self.check_token_limit = check_token_limit
        self.get_limit_error_message = get_limit_error_message

    def format_messages(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        supports_images: bool = False,
    ) -> List[dict]:
        """Format messages for LLM.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages
            supports_images: Whether model supports images

        Returns:
            Formatted message list
        """
        if system_msgs:
            formatted_system = fmt_msgs(system_msgs, supports_images)
            formatted_messages = formatted_system + fmt_msgs(messages, supports_images)
        else:
            formatted_messages = fmt_msgs(messages, supports_images)
        return formatted_messages

    def count_input_tokens(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
    ) -> int:
        """Calculate input token count.

        Args:
            messages: Formatted messages
            tools: Optional list of tools

        Returns:
            Total input token count
        """
        input_tokens = self.token_counter.count_message_tokens(messages)

        # If there are tools, calculate token count for tool descriptions
        if tools:
            tools_tokens = 0
            for tool in tools:
                tools_tokens += self.token_counter.count_tokens(str(tool))
            input_tokens += tools_tokens

        return input_tokens

    def check_limits(self, input_tokens: int) -> bool:
        """Check if token limits are exceeded.

        Args:
            input_tokens: Number of input tokens

        Returns:
            True if within limits

        Raises:
            TokenLimitExceeded: If token limits exceeded
        """
        from nura.core.exceptions import TokenLimitExceeded

        if not self.check_token_limit(input_tokens):
            error_message = self.get_limit_error_message(input_tokens)
            raise TokenLimitExceeded(error_message)
        return True

    def build_params(
        self,
        model: str,
        messages: List[dict],
        max_tokens: int,
        temperature: float,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
        previous_response_id: Optional[str] = None,
        supports_images: bool = False,
    ) -> Dict[str, Any]:
        """Build request parameters for Ark API.

        Args:
            model: Model identifier
            messages: Formatted messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            tools: Optional list of tools
            tool_choice: Optional tool choice
            previous_response_id: Previous response ID for caching
            supports_images: Whether model supports images

        Returns:
            Request parameters dictionary
        """
        # Get the Ark adapter
        adapter = ArkMessageAdapter()

        # Convert messages to Ark format using adapter
        ark_messages = adapter.format_for_provider(messages, tools, tool_choice)

        # Format tools using adapter
        ark_tools = adapter.format_tools(tools)

        # Calculate cache_ttl
        try:
            config_obj = get_config()
            cache_ttl = config_obj.llm.get(
                "default", config_obj.llm.get("default")
            ).cache_ttl
        except (AttributeError, KeyError):
            cache_ttl = 3600

        # Build request params
        params = {
            "model": model,
            "input": ark_messages,
            "tools": ark_tools,
            "tool_choice": tool_choice,
            "extra_body": {
                "expire_at": int(time.time()) + cache_ttl,
                "caching": {"type": "enabled"},
                "thinking": {"type": "disabled"},
            },
        }

        if previous_response_id:
            params["previous_response_id"] = previous_response_id
            # Except for the first call, tools should be None
            params["tools"] = None
            params["tool_choice"] = None

        if model in REASONING_MODELS:
            params["max_output_tokens"] = max_tokens
        else:
            params["max_output_tokens"] = max_tokens
            params["temperature"] = temperature

        params["stream"] = False

        return params

    def build_chat_params(
        self,
        model: str,
        messages: List[dict],
        max_tokens: int,
        temperature: float,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
        timeout: int = 300,
        stream: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Build request parameters for standard chat completion API.

        Args:
            model: Model identifier
            messages: Formatted messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            tools: Optional list of tools
            tool_choice: Optional tool choice
            timeout: Request timeout in seconds
            stream: Whether to stream the response
            **kwargs: Additional completion arguments

        Returns:
            Request parameters dictionary for chat.completions.create
        """
        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "timeout": timeout,
            **kwargs,
        }

        if model in REASONING_MODELS:
            params["max_completion_tokens"] = max_tokens
        else:
            params["max_tokens"] = max_tokens
            params["temperature"] = temperature

        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice

        params["stream"] = stream

        return params

    def parse_response(self, response: Any, adapter: Optional[Any] = None) -> Any:
        """Parse response from Ark API.

        Args:
            response: Raw API response
            adapter: Optional message adapter (defaults to ArkMessageAdapter)

        Returns:
            Parsed message
        """
        if adapter is None:
            adapter = ArkMessageAdapter()
        return adapter.parse_response(response)

    def extract_usage(self, response: Any) -> Optional[Dict[str, Any]]:
        """Extract usage information from response.

        Args:
            response: API response object

        Returns:
            Dictionary with usage info or None
        """
        if hasattr(response, "usage") and hasattr(response.usage, "input_tokens"):
            cached_tokens = 0
            if hasattr(response.usage, "input_tokens_details") and hasattr(
                response.usage.input_tokens_details, "cached_tokens"
            ):
                cached_tokens = response.usage.input_tokens_details.cached_tokens
            return {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cached_tokens": cached_tokens,
                "response_id": response.id,
                "expire_at": getattr(response, "expire_at", None),
            }
        return None
