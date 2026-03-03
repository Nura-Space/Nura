"""Tests for LLM cache module."""
import pytest
import time
from unittest.mock import MagicMock, AsyncMock, patch

from nura.llm.cache import ask_with_ark_cache
from nura.core.exceptions import TokenLimitExceeded


class TestAskWithArkCache:
    """Test cases for ask_with_ark_cache function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_basic_request(self):
        """Test basic cache request without session."""
        mock_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_token_counter.count_message_tokens.return_value = 100
        mock_token_counter.count_tokens.return_value = 50

        mock_response = MagicMock()
        mock_response.output = []
        mock_response.id = "response_123"
        mock_response.expire_at = int(time.time()) + 3600
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        mock_message = MagicMock()
        mock_message.content = "Hello"
        mock_message.role = "assistant"

        # Setup usage details
        mock_usage_details = MagicMock()
        mock_usage_details.cached_tokens = 0
        mock_response.usage.input_tokens_details = mock_usage_details

        # Mock message content item
        mock_content_item = MagicMock()
        mock_content_item.type = "output_text"
        mock_content_item.text = "Hello"
        mock_response.output = [mock_content_item]

        with patch("nura.llm.cache.ark.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = None

            with patch("nura.llm.request.RequestBuilder") as mock_builder_class:
                mock_builder = MagicMock()
                mock_builder.format_messages.return_value = [{"role": "user", "content": "test"}]
                mock_builder.count_input_tokens.return_value = 100
                mock_builder.check_limits.return_value = True
                mock_builder.build_params.return_value = {"model": "gpt-4"}
                mock_builder.parse_response.return_value = mock_message
                mock_builder.extract_usage.return_value = {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cached_tokens": 0,
                    "response_id": "response_123",
                    "expire_at": int(time.time()) + 3600,
                }
                mock_builder_class.return_value = mock_builder

                with patch("nura.llm.cache.ark.config"):
                    mock_client.responses.create = AsyncMock(return_value=mock_response)

                    result = await ask_with_ark_cache(
                        client=mock_client,
                        model="gpt-4",
                        messages=[{"role": "user", "content": "test"}],
                        token_counter=mock_token_counter,
                        check_token_limit=lambda x: True,
                        get_limit_error_message=lambda x: "Error",
                        max_tokens=1000,
                        temperature=0.7
                    )

                    assert result is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_token_limit_exceeded(self):
        """Test token limit exceeded error."""
        mock_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_token_counter.count_message_tokens.return_value = 200000

        with patch("nura.llm.cache.ark.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = None

            with patch("nura.llm.request.RequestBuilder") as mock_builder_class:
                mock_builder = MagicMock()
                mock_builder.format_messages.return_value = [{"role": "user", "content": "test"}]
                mock_builder.count_input_tokens.return_value = 200000
                mock_builder.check_limits.side_effect = TokenLimitExceeded("Token limit exceeded")
                mock_builder_class.return_value = mock_builder

                with patch("nura.llm.cache.ark.config"):
                    with pytest.raises(TokenLimitExceeded):
                        await ask_with_ark_cache(
                            client=mock_client,
                            model="gpt-4",
                            messages=[{"role": "user", "content": "test"}],
                            token_counter=mock_token_counter,
                            check_token_limit=lambda x: False,
                            get_limit_error_message=lambda x: "Token limit exceeded",
                            max_tokens=1000,
                            temperature=0.7
                        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_session_cache(self):
        """Test request with session cache."""
        mock_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_token_counter.count_message_tokens.return_value = 100

        mock_session = MagicMock()
        mock_session.response_id = "prev_response_123"
        mock_session.last_message_count = 2

        mock_response = MagicMock()
        mock_content_item = MagicMock()
        mock_content_item.type = "output_text"
        mock_content_item.text = "Response"
        mock_response.output = [mock_content_item]
        mock_response.id = "response_456"
        mock_response.expire_at = int(time.time()) + 3600
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_usage_details = MagicMock()
        mock_usage_details.cached_tokens = 50
        mock_response.usage.input_tokens_details = mock_usage_details

        mock_message = MagicMock()
        mock_message.content = "Response"

        with patch("nura.llm.cache.ark.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = mock_session

            with patch("nura.llm.request.RequestBuilder") as mock_builder_class:
                mock_builder = MagicMock()
                mock_builder.format_messages.return_value = [
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi"},
                    {"role": "user", "content": "test"}
                ]
                mock_builder.count_input_tokens.return_value = 100
                mock_builder.check_limits.return_value = True

                def build_params_side_effect(**kwargs):
                    return {"model": "gpt-4", "previous_response_id": kwargs.get("previous_response_id")}

                mock_builder.build_params.side_effect = build_params_side_effect
                mock_builder.parse_response.return_value = mock_message
                mock_builder.extract_usage.return_value = {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cached_tokens": 50,
                    "response_id": "response_456",
                    "expire_at": int(time.time()) + 3600,
                }
                mock_builder_class.return_value = mock_builder

                with patch("nura.llm.cache.ark.config"):
                    mock_client.responses.create = AsyncMock(return_value=mock_response)

                    result = await ask_with_ark_cache(
                        client=mock_client,
                        model="gpt-4",
                        messages=[{"role": "user", "content": "test"}],
                        token_counter=mock_token_counter,
                        check_token_limit=lambda x: True,
                        get_limit_error_message=lambda x: "Error",
                        max_tokens=1000,
                        temperature=0.7,
                        session_id="test_session"
                    )

                    call_kwargs = mock_client.responses.create.call_args.kwargs
                    assert call_kwargs.get("previous_response_id") == "prev_response_123"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_tools(self):
        """Test request with tools."""
        mock_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_token_counter.count_message_tokens.return_value = 100
        mock_token_counter.count_tokens.return_value = 50

        mock_response = MagicMock()
        mock_content_item = MagicMock()
        mock_content_item.type = "output_text"
        mock_content_item.text = "Response"
        mock_response.output = [mock_content_item]
        mock_response.id = "response_789"
        mock_response.expire_at = int(time.time()) + 3600
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        mock_message = MagicMock()
        mock_message.content = "Response"

        tools = [{"type": "function", "function": {"name": "test_tool", "description": "A test tool"}}]

        with patch("nura.llm.cache.ark.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = None

            with patch("nura.llm.request.RequestBuilder") as mock_builder_class:
                mock_builder = MagicMock()
                mock_builder.format_messages.return_value = [{"role": "user", "content": "test"}]
                mock_builder.count_input_tokens.return_value = 150  # including tools
                mock_builder.check_limits.return_value = True
                mock_builder.build_params.return_value = {"model": "gpt-4", "tools": tools}
                mock_builder.parse_response.return_value = mock_message
                mock_builder.extract_usage.return_value = {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cached_tokens": 0,
                    "response_id": "response_789",
                    "expire_at": int(time.time()) + 3600,
                }
                mock_builder_class.return_value = mock_builder

                with patch("nura.llm.cache.ark.config"):
                    mock_client.responses.create = AsyncMock(return_value=mock_response)

                    result = await ask_with_ark_cache(
                        client=mock_client,
                        model="gpt-4",
                        messages=[{"role": "user", "content": "test"}],
                        token_counter=mock_token_counter,
                        check_token_limit=lambda x: True,
                        get_limit_error_message=lambda x: "Error",
                        max_tokens=1000,
                        temperature=0.7,
                        tools=tools
                    )

                    call_kwargs = mock_client.responses.create.call_args.kwargs
                    assert call_kwargs.get("tools") is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_system_messages(self):
        """Test request with system messages."""
        mock_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_token_counter.count_message_tokens.return_value = 100

        mock_response = MagicMock()
        mock_content_item = MagicMock()
        mock_content_item.type = "output_text"
        mock_content_item.text = "Response"
        mock_response.output = [mock_content_item]
        mock_response.id = "response_abc"
        mock_response.expire_at = int(time.time()) + 3600
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_usage_details = MagicMock()
        mock_usage_details.cached_tokens = 0
        mock_response.usage.input_tokens_details = mock_usage_details

        mock_message = MagicMock()
        mock_message.content = "Response"

        system_msgs = [{"role": "system", "content": "You are helpful"}]

        with patch("nura.llm.cache.ark.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = None

            with patch("nura.llm.request.RequestBuilder") as mock_builder_class:
                mock_builder = MagicMock()
                mock_builder.format_messages.return_value = [
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "test"}
                ]
                mock_builder.count_input_tokens.return_value = 100
                mock_builder.check_limits.return_value = True
                mock_builder.build_params.return_value = {"model": "gpt-4"}
                mock_builder.parse_response.return_value = mock_message
                mock_builder.extract_usage.return_value = {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cached_tokens": 0,
                    "response_id": "response_abc",
                    "expire_at": int(time.time()) + 3600,
                }
                mock_builder_class.return_value = mock_builder

                with patch("nura.llm.cache.ark.config"):
                    mock_client.responses.create = AsyncMock(return_value=mock_response)

                    result = await ask_with_ark_cache(
                        client=mock_client,
                        model="gpt-4",
                        messages=[{"role": "user", "content": "test"}],
                        token_counter=mock_token_counter,
                        check_token_limit=lambda x: True,
                        get_limit_error_message=lambda x: "Error",
                        max_tokens=1000,
                        temperature=0.7,
                        system_msgs=system_msgs
                    )

                    # Verify format_messages was called with system_msgs
                    mock_builder.format_messages.assert_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_response(self):
        """Test handling of empty response."""
        mock_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_token_counter.count_message_tokens.return_value = 100

        mock_response = MagicMock()
        mock_response.output = []

        with patch("nura.llm.cache.ark.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = None

            with patch("nura.llm.request.RequestBuilder") as mock_builder_class:
                mock_builder = MagicMock()
                mock_builder.format_messages.return_value = []
                mock_builder.count_input_tokens.return_value = 100
                mock_builder.check_limits.return_value = True
                mock_builder.build_params.return_value = {"model": "gpt-4"}
                mock_builder.parse_response.return_value = None
                mock_builder.extract_usage.return_value = None
                mock_builder_class.return_value = mock_builder

                with patch("nura.llm.cache.ark.config"):
                    mock_client.responses.create = AsyncMock(return_value=mock_response)

                    result = await ask_with_ark_cache(
                        client=mock_client,
                        model="gpt-4",
                        messages=[],
                        token_counter=mock_token_counter,
                        check_token_limit=lambda x: True,
                        get_limit_error_message=lambda x: "Error",
                        max_tokens=1000,
                        temperature=0.7
                    )

                    assert result is None


class TestCacheStrategy:
    """Test cases for cache strategy configuration."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_strategy_full(self):
        """Test cache strategy 'full' - only sends new user messages after assistant."""
        mock_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_token_counter.count_message_tokens.return_value = 100

        mock_session = MagicMock()
        mock_session.response_id = "prev_response_123"
        mock_session.last_message_count = 2

        mock_response = MagicMock()
        mock_content_item = MagicMock()
        mock_content_item.type = "output_text"
        mock_content_item.text = "Response"
        mock_response.output = [mock_content_item]
        mock_response.id = "response_456"
        mock_response.expire_at = int(time.time()) + 3600
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_usage_details = MagicMock()
        mock_usage_details.cached_tokens = 30
        mock_response.usage.input_tokens_details = mock_usage_details

        mock_message = MagicMock()
        mock_message.content = "Response"

        full_history = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]

        expected_input = [{"role": "user", "content": "How are you?"}]

        mock_config = MagicMock()
        mock_config.llm = {"cache_strategy": "full"}

        with patch("nura.llm.cache.ark.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = mock_session

            with patch("nura.llm.request.RequestBuilder") as mock_builder_class:
                mock_builder = MagicMock()
                mock_builder.format_messages.return_value = full_history
                mock_builder.count_input_tokens.return_value = 100
                mock_builder.check_limits.return_value = True
                mock_builder.build_params.return_value = {"model": "gpt-4", "previous_response_id": "prev_response_123"}
                mock_builder.parse_response.return_value = mock_message
                mock_builder.extract_usage.return_value = {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cached_tokens": 30,
                    "response_id": "response_456",
                    "expire_at": int(time.time()) + 3600,
                }
                mock_builder_class.return_value = mock_builder

                with patch("nura.llm.cache.ark.config", mock_config):
                    mock_client.responses.create = AsyncMock(return_value=mock_response)

                    result = await ask_with_ark_cache(
                        client=mock_client,
                        model="gpt-4",
                        messages=[{"role": "user", "content": "How are you?"}],
                        token_counter=mock_token_counter,
                        check_token_limit=lambda x: True,
                        get_limit_error_message=lambda x: "Error",
                        max_tokens=1000,
                        temperature=0.7,
                        session_id="test_session"
                    )

                    call_kwargs = mock_client.responses.create.call_args.kwargs
                    assert call_kwargs.get("previous_response_id") == "prev_response_123"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_strategy_input_only(self):
        """Test cache strategy 'input_only' - includes previous assistant + new user."""
        mock_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_token_counter.count_message_tokens.return_value = 100

        mock_session = MagicMock()
        mock_session.response_id = "prev_response_123"
        mock_session.last_message_count = 2

        mock_response = MagicMock()
        mock_content_item = MagicMock()
        mock_content_item.type = "output_text"
        mock_content_item.text = "Response"
        mock_response.output = [mock_content_item]
        mock_response.id = "response_456"
        mock_response.expire_at = int(time.time()) + 3600
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_usage_details = MagicMock()
        mock_usage_details.cached_tokens = 30
        mock_response.usage.input_tokens_details = mock_usage_details

        mock_message = MagicMock()
        mock_message.content = "Response"

        full_history = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]

        expected_input = [
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]

        mock_config = MagicMock()
        mock_config.llm = {"cache_strategy": "input_only"}

        with patch("nura.llm.cache.ark.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = mock_session

            with patch("nura.llm.request.RequestBuilder") as mock_builder_class:
                mock_builder = MagicMock()
                mock_builder.format_messages.return_value = full_history
                mock_builder.count_input_tokens.return_value = 100
                mock_builder.check_limits.return_value = True
                mock_builder.build_params.return_value = {"model": "gpt-4", "previous_response_id": "prev_response_123"}
                mock_builder.parse_response.return_value = mock_message
                mock_builder.extract_usage.return_value = {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cached_tokens": 30,
                    "response_id": "response_456",
                    "expire_at": int(time.time()) + 3600,
                }
                mock_builder_class.return_value = mock_builder

                with patch("nura.llm.cache.ark.config", mock_config):
                    mock_client.responses.create = AsyncMock(return_value=mock_response)

                    result = await ask_with_ark_cache(
                        client=mock_client,
                        model="gpt-4",
                        messages=[{"role": "user", "content": "How are you?"}],
                        token_counter=mock_token_counter,
                        check_token_limit=lambda x: True,
                        get_limit_error_message=lambda x: "Error",
                        max_tokens=1000,
                        temperature=0.7,
                        session_id="test_session"
                    )

                    call_kwargs = mock_client.responses.create.call_args.kwargs
                    assert call_kwargs.get("previous_response_id") == "prev_response_123"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_strategy_default_is_input_only(self):
        """Test default cache strategy is 'input_only' when not specified."""
        mock_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_token_counter.count_message_tokens.return_value = 100

        mock_session = MagicMock()
        mock_session.response_id = "prev_response_123"
        mock_session.last_message_count = 2

        mock_response = MagicMock()
        mock_content_item = MagicMock()
        mock_content_item.type = "output_text"
        mock_content_item.text = "Response"
        mock_response.output = [mock_content_item]
        mock_response.id = "response_456"
        mock_response.expire_at = int(time.time()) + 3600
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_usage_details = MagicMock()
        mock_usage_details.cached_tokens = 30
        mock_response.usage.input_tokens_details = mock_usage_details

        mock_message = MagicMock()
        mock_message.content = "Response"

        full_history = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]

        mock_config = MagicMock()
        mock_config.llm = MagicMock()
        mock_config.llm.get = lambda key, default: default

        with patch("nura.llm.cache.ark.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = mock_session

            with patch("nura.llm.request.RequestBuilder") as mock_builder_class:
                mock_builder = MagicMock()
                mock_builder.format_messages.return_value = full_history
                mock_builder.count_input_tokens.return_value = 100
                mock_builder.check_limits.return_value = True
                mock_builder.build_params.return_value = {"model": "gpt-4", "previous_response_id": "prev_response_123"}
                mock_builder.parse_response.return_value = mock_message
                mock_builder.extract_usage.return_value = {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cached_tokens": 30,
                    "response_id": "response_456",
                    "expire_at": int(time.time()) + 3600,
                }
                mock_builder_class.return_value = mock_builder

                with patch("nura.llm.cache.ark.config", mock_config):
                    mock_client.responses.create = AsyncMock(return_value=mock_response)

                    result = await ask_with_ark_cache(
                        client=mock_client,
                        model="gpt-4",
                        messages=[{"role": "user", "content": "How are you?"}],
                        token_counter=mock_token_counter,
                        check_token_limit=lambda x: True,
                        get_limit_error_message=lambda x: "Error",
                        max_tokens=1000,
                        temperature=0.7,
                        session_id="test_session"
                    )

                    mock_builder.format_messages.assert_called()
