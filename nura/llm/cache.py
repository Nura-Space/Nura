"""Caching utilities for LLM providers."""

import time
from typing import Any, List, Optional, Union

from nura.core.cache import cache_manager
from nura.core.config import config
from nura.core.exceptions import TokenLimitExceeded
from nura.core.logger import logger
from nura.core.schema import Message

from nura.llm.adapters import ArkMessageAdapter
from nura.llm.constants import REASONING_MODELS
from nura.llm.message import format_messages
from nura.llm.token_counter import TokenCounter


async def ask_with_ark_cache(
    client: Any,
    model: str,
    messages: List[Union[dict, Message]],
    token_counter: TokenCounter,
    check_token_limit: Any,
    get_limit_error_message: Any,
    max_tokens: int,
    temperature: float,
    system_msgs: Optional[List[Union[dict, Message]]] = None,
    tools: Optional[List[dict]] = None,
    tool_choice: Optional[Union[str, dict]] = None,
    session_id: Optional[str] = None,
    supports_images: bool = False,
) -> Any:
    """Handle LLM requests with Ark caching via /responses endpoint.

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
    # Get the Ark adapter
    adapter = ArkMessageAdapter()

    # Format messages
    if system_msgs:
        formatted_system = format_messages(system_msgs, supports_images)
        formatted_messages = formatted_system + format_messages(
            messages, supports_images
        )
    else:
        formatted_messages = format_messages(messages, supports_images)

    # Check Cache
    session_data = cache_manager.get_session(session_id)
    previous_response_id = None
    input_msgs = []

    # Get cache strategy from config (default: "input_only")
    try:
        cache_strategy = config.llm.get("cache_strategy", "input_only")
    except (AttributeError, KeyError):
        cache_strategy = "input_only"

    # Determine caching strategy based on config
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
            # This way caching only caches the input, not the assistant response
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

    # Convert messages to Ark format using adapter
    ark_messages = adapter.format_for_provider(input_msgs, tools, tool_choice)

    # Calculate input token count
    input_tokens = token_counter.count_message_tokens(ark_messages)

    # If there are tools, calculate token count for tool descriptions
    tools_tokens = 0
    if tools:
        for tool in tools:
            tools_tokens += token_counter.count_tokens(str(tool))

    input_tokens += tools_tokens

    # Check if token limits are exceeded
    if not check_token_limit(input_tokens):
        error_message = get_limit_error_message(input_tokens)
        raise TokenLimitExceeded(error_message)

    # Format tools using adapter
    ark_tools = adapter.format_tools(tools)

    # Calculate cache_ttl
    try:
        cache_ttl = config.llm["default"].cache_ttl
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
        # Requirement: Except for the first call, tools should be None
        params["tools"] = None
        params["tool_choice"] = None

    if model in REASONING_MODELS:
        params["max_output_tokens"] = max_tokens
    else:
        params["max_output_tokens"] = max_tokens
        params["temperature"] = temperature

    # Debug logging
    logger.info(f"previous_response_id: {previous_response_id}")
    for msg in ark_messages:
        # Create a copy to avoid modifying the original message
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

    params["stream"] = False  # Always use non-streaming for tool requests

    # Make the request
    response = await client.responses.create(**params)

    # Check if response is valid
    if not response.output:
        logger.info(response)
        return None

    # Parse response using adapter
    parsed_message = adapter.parse_response(response)

    # Update token counts (if update_token_count is available)
    if hasattr(response, "usage") and hasattr(response.usage, "input_tokens"):
        cached_tokens = 0
        if hasattr(response.usage, "input_tokens_details") and hasattr(
            response.usage.input_tokens_details, "cached_tokens"
        ):
            cached_tokens = response.usage.input_tokens_details.cached_tokens
        return {
            "message": parsed_message,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cached_tokens": cached_tokens,
            "response_id": response.id,
            "expire_at": response.expire_at,
            "message_count": len(formatted_messages),
        }

    return parsed_message
