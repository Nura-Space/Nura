"""Ark (Volcengine) cache implementation."""
# pylint: disable=duplicate-code
# The factory method call here intentionally mirrors the LLMRequestParams.create() signature.
# This is a necessary pattern for creating parameterized objects.

from typing import Any, Callable, List, Optional, Union

from nura.core.cache import cache_manager
from nura.core.config import config
from nura.core.logger import logger, context_log
from nura.core.schema import Message

from nura.llm.cache.base import BaseCache, LLMRequestParams
from nura.llm.token_counter import TokenCounter


async def ask_with_ark_cache(
    client: Any,
    model: str,
    messages: List[Union[dict, Message]],
    token_counter: TokenCounter,
    check_token_limit: Callable[[int], bool],
    get_limit_error_message: Callable[[int], str],
    max_tokens: int,
    temperature: float,
    system_msgs: Optional[List[Union[dict, Message]]] = None,
    tools: Optional[List[dict]] = None,
    tool_choice: Optional[Union[str, dict]] = None,
    session_id: Optional[str] = None,
    supports_images: bool = False,
) -> Any:
    """Handle LLM requests with Ark caching via /responses endpoint.

    This is a backward-compatible wrapper using the new cache architecture.

    Args:
        client: The async LLM client (e.g., AsyncOpenAI)
        model: Model identifier
        messages: List of conversation messages
        token_counter: TokenCounter instance for counting tokens
        check_token_limit: Function to check if token limit is exceeded
        get_limit_error_message: Function to generate error message
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        system_msgs: Optional system messages
        tools: Optional list of tools
        tool_choice: Optional tool choice
        session_id: Session ID for context caching
        supports_images: Whether model supports images

    Returns:
        ChatCompletionMessage in standard format

    Raises:
        TokenLimitExceeded: If token limits exceeded
    """
    # Import here to avoid circular imports
    from nura.llm.request import RequestBuilder

    # Create request builder
    request_builder = RequestBuilder(
        token_counter=token_counter,
        check_token_limit=check_token_limit,
        get_limit_error_message=get_limit_error_message,
    )

    # Create cache instance and use it
    cache = ArkCache()

    params = LLMRequestParams.create(
        client=client,
        model=model,
        messages=messages,
        request_builder=request_builder,
        max_tokens=max_tokens,
        temperature=temperature,
        system_msgs=system_msgs,
        tools=tools,
        tool_choice=tool_choice,
        session_id=session_id,
        supports_images=supports_images,
    )

    return await cache.ask(params)


class ArkCache(BaseCache):
    """Cache implementation for Volcengine Ark (volces.com) provider."""

    async def ask(
        self,
        params: LLMRequestParams,
    ) -> Any:
        """Execute LLM request with Ark caching via /responses endpoint.

        Args:
            params: LLM request parameters

        Returns:
            ChatCompletionMessage in standard format or dict with metadata
        """
        # Format messages using request builder
        formatted_messages = params.request_builder.format_messages(
            params.messages, params.system_msgs, params.supports_images
        )

        # Get cache strategy from config (default: "input_only")
        cache_strategy = self._get_cache_strategy()

        # Check cache and get input messages
        session_data = cache_manager.get_session(params.session_id)
        previous_response_id = None
        input_msgs = []

        if session_data:
            previous_response_id = session_data.response_id
            last_count = session_data.last_message_count

            if cache_strategy == "full":
                # Strategy 1: Cache input + output (original behavior)
                # Only send new user messages after the previous assistant response
                start_index = last_count + 1
            else:
                # Strategy 2: Only cache input content (default)
                # Include the previous assistant message + new user message
                start_index = last_count

            if len(formatted_messages) > start_index:
                input_msgs = formatted_messages[start_index:]
            else:
                if formatted_messages:
                    input_msgs = [formatted_messages[-1]]
                else:
                    input_msgs = []
        else:
            input_msgs = formatted_messages

        # Count input tokens
        input_tokens = params.request_builder.count_input_tokens(input_msgs, params.tools)

        # Check token limits
        params.request_builder.check_limits(input_tokens)

        # Build request params
        request_params = params.request_builder.build_params(
            model=params.model,
            messages=input_msgs,
            max_tokens=params.max_tokens,
            temperature=params.temperature,
            tools=params.tools,
            tool_choice=params.tool_choice,
            previous_response_id=previous_response_id,
            supports_images=params.supports_images,
        )

        # Debug logging
        self._log_request(previous_response_id, input_msgs)

        # Make the request
        response = await params.client.responses.create(**request_params)

        # Check if response is valid
        if not response.output:
            logger.info(response)
            return None

        # Parse response
        parsed_message = params.request_builder.parse_response(response)

        # Extract usage info
        usage_info = params.request_builder.extract_usage(response)

        if usage_info:
            return {
                "message": parsed_message,
                "input_tokens": usage_info["input_tokens"],
                "output_tokens": usage_info["output_tokens"],
                "cached_tokens": usage_info["cached_tokens"],
                "response_id": usage_info["response_id"],
                "expire_at": usage_info["expire_at"],
                "message_count": len(formatted_messages),
            }

        return parsed_message

    def supports_cache(self, base_url: Optional[str]) -> bool:
        """Check if this cache supports the given base_url.

        Args:
            base_url: The API base URL

        Returns:
            True if the URL indicates Ark provider
        """
        if not base_url:
            return False
        return "volces.com" in base_url

    def _get_cache_strategy(self) -> str:
        """Get cache strategy from config.

        Returns:
            Cache strategy string
        """
        try:
            return config.llm.get("cache_strategy", "input_only")
        except (AttributeError, KeyError):
            return "input_only"

    def _log_request(self, previous_response_id: Optional[str], messages: List[dict]) -> None:
        """Log request details for debugging.

        Args:
            previous_response_id: Previous response ID
            messages: Input messages
        """
        # Log truncated version to terminal
        logger.info(f"previous_response_id: {previous_response_id}")
        for msg in messages:
            log_msg = dict(msg) if msg else {}
            if (
                "content" in log_msg
                and isinstance(log_msg["content"], str)
                and len(log_msg["content"]) > 10
            ):
                log_msg["content"] = log_msg["content"][:10] + "..."
            if (
                "base64_image" in log_msg
                and isinstance(log_msg["base64_image"], str)
                and len(log_msg["base64_image"]) > 10
            ):
                log_msg["content"] = log_msg["base64_image"][:10] + "..."
            logger.info(log_msg)

        # Log complete version to context_*.log file
        context_log(f"previous_response_id: {previous_response_id}")
        for msg in messages:
            context_log(str(msg))
