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

        with patch("nura.llm.cache.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = None

            with patch("nura.llm.cache.ArkMessageAdapter") as mock_adapter_class:
                mock_adapter = MagicMock()
                mock_adapter.format_for_provider.return_value = [{"role": "user", "content": "test"}]
                mock_adapter.format_tools.return_value = None
                mock_adapter.parse_response.return_value = mock_message
                mock_adapter_class.return_value = mock_adapter

                with patch("nura.llm.cache.format_messages") as mock_format:
                    mock_format.return_value = [{"role": "user", "content": "test"}]

                    with patch("nura.llm.cache.config"):
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

        with patch("nura.llm.cache.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = None  # No session, go to else branch

            with patch("nura.llm.cache.ArkMessageAdapter") as mock_adapter_class:
                mock_adapter = MagicMock()
                mock_adapter.format_for_provider.return_value = [{"role": "user", "content": "test"}]
                mock_adapter.format_tools.return_value = None
                mock_adapter_class.return_value = mock_adapter

                with patch("nura.llm.cache.format_messages") as mock_format:
                    mock_format.return_value = [{"role": "user", "content": "test"}]

                    with patch("nura.llm.cache.config"):
                        with pytest.raises(TokenLimitExceeded):
                            await ask_with_ark_cache(
                                client=mock_client,
                                model="gpt-4",
                                messages=[{"role": "user", "content": "test"}],
                                token_counter=mock_token_counter,
                                check_token_limit=lambda x: False,  # Always return False
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

        # Create session data with previous response
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

        with patch("nura.llm.cache.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = mock_session

            with patch("nura.llm.cache.ArkMessageAdapter") as mock_adapter_class:
                mock_adapter = MagicMock()
                mock_adapter.format_for_provider.return_value = [{"role": "user", "content": "test"}]
                mock_adapter.format_tools.return_value = None
                mock_adapter.parse_response.return_value = mock_message
                mock_adapter_class.return_value = mock_adapter

                with patch("nura.llm.cache.format_messages") as mock_format:
                    mock_format.return_value = [
                        {"role": "system", "content": "You are helpful"},
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hi"},
                        {"role": "user", "content": "test"}
                    ]

                    with patch("nura.llm.cache.config"):
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

                        # Verify previous_response_id was passed
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

        with patch("nura.llm.cache.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = None

            with patch("nura.llm.cache.ArkMessageAdapter") as mock_adapter_class:
                mock_adapter = MagicMock()
                mock_adapter.format_for_provider.return_value = [{"role": "user", "content": "test"}]
                mock_adapter.format_tools.return_value = tools
                mock_adapter.parse_response.return_value = mock_message
                mock_adapter_class.return_value = mock_adapter

                with patch("nura.llm.cache.format_messages") as mock_format:
                    mock_format.return_value = [{"role": "user", "content": "test"}]

                    with patch("nura.llm.cache.config"):
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

                        # Verify tools were passed
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

        with patch("nura.llm.cache.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = None

            with patch("nura.llm.cache.ArkMessageAdapter") as mock_adapter_class:
                mock_adapter = MagicMock()
                mock_adapter.format_for_provider.return_value = [{"role": "user", "content": "test"}]
                mock_adapter.format_tools.return_value = None
                mock_adapter.parse_response.return_value = mock_message
                mock_adapter_class.return_value = mock_adapter

                with patch("nura.llm.cache.format_messages") as mock_format:
                    mock_format.return_value = [
                        {"role": "system", "content": "You are helpful"},
                        {"role": "user", "content": "test"}
                    ]

                    with patch("nura.llm.cache.config"):
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

                        # Verify format_messages was called twice (system + messages)
                        assert mock_format.call_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_response(self):
        """Test handling of empty response."""
        mock_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_token_counter.count_message_tokens.return_value = 100

        mock_response = MagicMock()
        mock_response.output = []  # Empty response

        with patch("nura.llm.cache.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = None

            with patch("nura.llm.cache.ArkMessageAdapter") as mock_adapter_class:
                mock_adapter = MagicMock()
                mock_adapter.format_for_provider.return_value = []
                mock_adapter.format_tools.return_value = None
                mock_adapter_class.return_value = mock_adapter

                with patch("nura.llm.cache.format_messages") as mock_format:
                    mock_format.return_value = []

                    with patch("nura.llm.cache.config"):
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

                        # Empty response should return None
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

        # Session with previous response
        mock_session = MagicMock()
        mock_session.response_id = "prev_response_123"
        mock_session.last_message_count = 2  # After first user message

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

        # Full message history: [system, user1, assistant1, user2]
        full_history = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]

        # With strategy 'full', only user2 should be sent
        expected_input = [{"role": "user", "content": "How are you?"}]

        mock_config = MagicMock()
        mock_config.llm = {"cache_strategy": "full"}

        with patch("nura.llm.cache.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = mock_session

            with patch("nura.llm.cache.ArkMessageAdapter") as mock_adapter_class:
                mock_adapter = MagicMock()
                mock_adapter.format_for_provider.return_value = expected_input
                mock_adapter.format_tools.return_value = None
                mock_adapter.parse_response.return_value = mock_message
                mock_adapter_class.return_value = mock_adapter

                with patch("nura.llm.cache.format_messages") as mock_format:
                    mock_format.return_value = full_history

                    with patch("nura.llm.cache.config", mock_config):
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

                        # Verify previous_response_id was passed
                        call_kwargs = mock_client.responses.create.call_args.kwargs
                        assert call_kwargs.get("previous_response_id") == "prev_response_123"

                        # Verify only new user message was sent (strategy: full)
                        mock_adapter.format_for_provider.assert_called_once()
                        call_args = mock_adapter.format_for_provider.call_args[0][0]
                        assert call_args == expected_input

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_strategy_input_only(self):
        """Test cache strategy 'input_only' - includes previous assistant + new user."""
        mock_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_token_counter.count_message_tokens.return_value = 100

        # Session with previous response
        mock_session = MagicMock()
        mock_session.response_id = "prev_response_123"
        mock_session.last_message_count = 2  # After first user message

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

        # Full message history: [system, user1, assistant1, user2]
        full_history = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]

        # With strategy 'input_only', should include assistant1 + user2
        expected_input = [
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]

        mock_config = MagicMock()
        mock_config.llm = {"cache_strategy": "input_only"}

        with patch("nura.llm.cache.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = mock_session

            with patch("nura.llm.cache.ArkMessageAdapter") as mock_adapter_class:
                mock_adapter = MagicMock()
                mock_adapter.format_for_provider.return_value = expected_input
                mock_adapter.format_tools.return_value = None
                mock_adapter.parse_response.return_value = mock_message
                mock_adapter_class.return_value = mock_adapter

                with patch("nura.llm.cache.format_messages") as mock_format:
                    mock_format.return_value = full_history

                    with patch("nura.llm.cache.config", mock_config):
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

                        # Verify previous_response_id was passed
                        call_kwargs = mock_client.responses.create.call_args.kwargs
                        assert call_kwargs.get("previous_response_id") == "prev_response_123"

                        # Verify assistant + new user message was sent (strategy: input_only)
                        mock_adapter.format_for_provider.assert_called_once()
                        call_args = mock_adapter.format_for_provider.call_args[0][0]
                        assert call_args == expected_input

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_strategy_default_is_input_only(self):
        """Test default cache strategy is 'input_only' when not specified."""
        mock_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_token_counter.count_message_tokens.return_value = 100

        # Session with previous response
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

        # With default strategy (input_only), should include assistant1 + user2
        expected_input = [
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]

        # Config without cache_strategy (should default to input_only)
        mock_config = MagicMock()
        mock_config.llm = MagicMock()
        mock_config.llm.get = lambda key, default: default  # Returns default for any key

        with patch("nura.llm.cache.cache_manager") as mock_cache:
            mock_cache.get_session.return_value = mock_session

            with patch("nura.llm.cache.ArkMessageAdapter") as mock_adapter_class:
                mock_adapter = MagicMock()
                mock_adapter.format_for_provider.return_value = expected_input
                mock_adapter.format_tools.return_value = None
                mock_adapter.parse_response.return_value = mock_message
                mock_adapter_class.return_value = mock_adapter

                with patch("nura.llm.cache.format_messages") as mock_format:
                    mock_format.return_value = full_history

                    with patch("nura.llm.cache.config", mock_config):
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

                        # Verify default strategy uses input_only logic
                        mock_adapter.format_for_provider.assert_called_once()
                        call_args = mock_adapter.format_for_provider.call_args[0][0]
                        assert call_args == expected_input
