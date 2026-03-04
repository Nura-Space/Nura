"""Tests for LLM client module."""
import pytest
from unittest.mock import MagicMock, patch

from nura.llm.client import LLM


class TestLLMClient:
    """Test cases for LLM client."""

    @pytest.fixture
    def mock_llm_config(self):
        """Create mock LLM config."""
        config = MagicMock()
        config.model = "gpt-4"
        config.max_tokens = 1000
        config.temperature = 0.7
        config.api_type = "openai"
        config.api_key = "test-key"
        config.api_version = "v1"
        config.base_url = "https://api.openai.com/v1"
        config.max_input_tokens = 100000
        return config

    @pytest.mark.unit
    def test_singleton_pattern(self):
        """Test that LLM uses singleton pattern."""
        # Clear instances
        LLM._instances = {}

        with patch("nura.llm.client.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_config.llm = {
                "default": MagicMock(
                    model="gpt-4",
                    max_tokens=1000,
                    temperature=0.7,
                    api_type="openai",
                    api_key="test-key",
                    api_version="v1",
                    base_url="https://api.openai.com/v1",
                    max_input_tokens=100000
                )
            }
            mock_get_config.return_value = mock_config

            llm1 = LLM("default")
            llm2 = LLM("default")

            assert llm1 is llm2

    @pytest.mark.unit
    def test_initialization(self):
        """Test LLM initialization."""
        LLM._instances = {}

        with patch("nura.llm.client.get_config") as mock_get_config:
            mock_llm_cfg = MagicMock()
            mock_llm_cfg.model = "gpt-4"
            mock_llm_cfg.max_tokens = 1000
            mock_llm_cfg.temperature = 0.7
            mock_llm_cfg.api_type = "openai"
            mock_llm_cfg.api_key = "test-key"
            mock_llm_cfg.api_version = "v1"
            mock_llm_cfg.base_url = "https://api.openai.com/v1"
            mock_llm_cfg.max_input_tokens = 100000

            mock_config = MagicMock()
            mock_config.llm = {"default": mock_llm_cfg}
            mock_get_config.return_value = mock_config

            with patch("nura.llm.client.tiktoken") as mock_tiktoken:
                mock_encoder = MagicMock()
                mock_encoder.encode.return_value = [1, 2, 3]
                mock_tiktoken.encoding_for_model.return_value = mock_encoder

                with patch("nura.llm.client.AsyncOpenAI"):
                    with patch("nura.llm.client.get_message_adapter"):
                        llm = LLM("default")

                        assert llm.model == "gpt-4"
                        assert llm.max_tokens == 1000
                        assert llm.temperature == 0.7
                        assert llm.api_type == "openai"

    @pytest.mark.unit
    def test_count_tokens(self):
        """Test token counting."""
        LLM._instances = {}

        with patch("nura.llm.client.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            mock_llm_cfg = MagicMock()
            mock_llm_cfg.model = "gpt-4"
            mock_llm_cfg.max_tokens = 1000
            mock_llm_cfg.temperature = 0.7
            mock_llm_cfg.api_type = "openai"
            mock_llm_cfg.api_key = "test-key"
            mock_llm_cfg.api_version = "v1"
            mock_llm_cfg.base_url = "https://api.openai.com/v1"
            mock_llm_cfg.max_input_tokens = 100000
            mock_config.llm = {"default": mock_llm_cfg}

            with patch("nura.llm.client.tiktoken") as mock_tiktoken:
                mock_encoder = MagicMock()
                mock_encoder.encode.return_value = [1, 2, 3, 4, 5]
                mock_tiktoken.encoding_for_model.return_value = mock_encoder

                with patch("nura.llm.client.AsyncOpenAI"):
                    with patch("nura.llm.client.get_message_adapter"):
                        llm = LLM("default")

                        count = llm.count_tokens("Hello world")

                        assert count == 5

    @pytest.mark.unit
    def test_count_message_tokens(self):
        """Test message token counting."""
        LLM._instances = {}

        with patch("nura.llm.client.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            mock_llm_cfg = MagicMock()
            mock_llm_cfg.model = "gpt-4"
            mock_llm_cfg.max_tokens = 1000
            mock_llm_cfg.temperature = 0.7
            mock_llm_cfg.api_type = "openai"
            mock_llm_cfg.api_key = "test-key"
            mock_llm_cfg.api_version = "v1"
            mock_llm_cfg.base_url = "https://api.openai.com/v1"
            mock_llm_cfg.max_input_tokens = 100000
            mock_config.llm = {"default": mock_llm_cfg}

            with patch("nura.llm.client.tiktoken") as mock_tiktoken:
                mock_encoder = MagicMock()
                mock_encoder.encode.return_value = [1, 2, 3]
                mock_tiktoken.encoding_for_model.return_value = mock_encoder

                with patch("nura.llm.client.AsyncOpenAI"):
                    with patch("nura.llm.client.get_message_adapter"):
                        llm = LLM("default")

                        messages = [
                            {"role": "user", "content": "Hello"},
                            {"role": "assistant", "content": "Hi there"}
                        ]

                        count = llm.count_message_tokens(messages)

                        assert count > 0

    @pytest.mark.unit
    def test_check_token_limit_within_limit(self):
        """Test token limit check when within limit."""
        LLM._instances = {}

        with patch("nura.llm.client.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            mock_llm_cfg = MagicMock()
            mock_llm_cfg.model = "gpt-4"
            mock_llm_cfg.max_tokens = 1000
            mock_llm_cfg.temperature = 0.7
            mock_llm_cfg.api_type = "openai"
            mock_llm_cfg.api_key = "test-key"
            mock_llm_cfg.api_version = "v1"
            mock_llm_cfg.base_url = "https://api.openai.com/v1"
            mock_llm_cfg.max_input_tokens = 100000
            mock_config.llm = {"default": mock_llm_cfg}

            with patch("nura.llm.client.tiktoken") as mock_tiktoken:
                mock_encoder = MagicMock()
                mock_encoder.encode.return_value = []
                mock_tiktoken.encoding_for_model.return_value = mock_encoder

                with patch("nura.llm.client.AsyncOpenAI"):
                    with patch("nura.llm.client.get_message_adapter"):
                        llm = LLM("default")
                        llm.max_input_tokens = 100000

                        result = llm.check_token_limit(50000)

                        assert result is True

    @pytest.mark.unit
    def test_check_token_limit_exceeds(self):
        """Test token limit check when exceeding limit."""
        LLM._instances = {}

        with patch("nura.llm.client.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            mock_llm_cfg = MagicMock()
            mock_llm_cfg.model = "gpt-4"
            mock_llm_cfg.max_tokens = 1000
            mock_llm_cfg.temperature = 0.7
            mock_llm_cfg.api_type = "openai"
            mock_llm_cfg.api_key = "test-key"
            mock_llm_cfg.api_version = "v1"
            mock_llm_cfg.base_url = "https://api.openai.com/v1"
            mock_llm_cfg.max_input_tokens = 100000
            mock_config.llm = {"default": mock_llm_cfg}

            with patch("nura.llm.client.tiktoken") as mock_tiktoken:
                mock_encoder = MagicMock()
                mock_encoder.encode.return_value = []
                mock_tiktoken.encoding_for_model.return_value = mock_encoder

                with patch("nura.llm.client.AsyncOpenAI"):
                    with patch("nura.llm.client.get_message_adapter"):
                        llm = LLM("default")
                        llm.max_input_tokens = 100000

                        result = llm.check_token_limit(150000)

                        assert result is False

    @pytest.mark.unit
    def test_get_limit_error_message(self):
        """Test error message generation."""
        LLM._instances = {}

        with patch("nura.llm.client.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            mock_llm_cfg = MagicMock()
            mock_llm_cfg.model = "gpt-4"
            mock_llm_cfg.max_tokens = 1000
            mock_llm_cfg.temperature = 0.7
            mock_llm_cfg.api_type = "openai"
            mock_llm_cfg.api_key = "test-key"
            mock_llm_cfg.api_version = "v1"
            mock_llm_cfg.base_url = "https://api.openai.com/v1"
            mock_llm_cfg.max_input_tokens = 100000
            mock_config.llm = {"default": mock_llm_cfg}

            with patch("nura.llm.client.tiktoken") as mock_tiktoken:
                mock_encoder = MagicMock()
                mock_encoder.encode.return_value = []
                mock_tiktoken.encoding_for_model.return_value = mock_encoder

                with patch("nura.llm.client.AsyncOpenAI"):
                    with patch("nura.llm.client.get_message_adapter"):
                        llm = LLM("default")

                        message = llm.get_limit_error_message(150000)

                        assert "150000" in message

    @pytest.mark.unit
    def test_has_ark_cached(self):
        """Test _has_ark_cached method."""
        LLM._instances = {}

        with patch("nura.llm.client.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            mock_llm_cfg = MagicMock()
            mock_llm_cfg.model = "gpt-4"
            mock_llm_cfg.max_tokens = 1000
            mock_llm_cfg.temperature = 0.7
            mock_llm_cfg.api_type = "openai"
            mock_llm_cfg.api_key = "test-key"
            mock_llm_cfg.api_version = "v1"
            mock_llm_cfg.base_url = "https://api.openai.com/v1"
            mock_llm_cfg.max_input_tokens = 100000
            mock_config.llm = {"default": mock_llm_cfg}

            with patch("nura.llm.client.tiktoken") as mock_tiktoken:
                mock_encoder = MagicMock()
                mock_encoder.encode.return_value = []
                mock_tiktoken.encoding_for_model.return_value = mock_encoder

                with patch("nura.llm.client.AsyncOpenAI"):
                    with patch("nura.llm.client.get_message_adapter"):
                        with patch("nura.llm.client.is_ark_provider") as mock_is_ark:
                            mock_is_ark.return_value = True
                            llm = LLM("default")

                            result = llm._has_ark_cached()

                            assert result is True


class TestLLMClientFormatMessages:
    """Test message formatting."""

    @pytest.fixture
    def mock_llm_config(self):
        config = MagicMock()
        config.model = "gpt-4"
        config.max_tokens = 1000
        config.temperature = 0.7
        config.api_type = "openai"
        config.api_key = "test-key"
        config.api_version = "v1"
        config.base_url = "https://api.openai.com/v1"
        config.max_input_tokens = 100000
        return config

    @pytest.mark.unit
    def test_format_messages(self):
        """Test format_messages method."""
        LLM._instances = {}

        with patch("nura.llm.client.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            mock_llm_cfg = MagicMock()
            mock_llm_cfg.model = "gpt-4"
            mock_llm_cfg.max_tokens = 1000
            mock_llm_cfg.temperature = 0.7
            mock_llm_cfg.api_type = "openai"
            mock_llm_cfg.api_key = "test-key"
            mock_llm_cfg.api_version = "v1"
            mock_llm_cfg.base_url = "https://api.openai.com/v1"
            mock_llm_cfg.max_input_tokens = 100000
            mock_config.llm = {"default": mock_llm_cfg}

            with patch("nura.llm.client.tiktoken") as mock_tiktoken:
                mock_encoder = MagicMock()
                mock_encoder.encode.return_value = []
                mock_tiktoken.encoding_for_model.return_value = mock_encoder

                with patch("nura.llm.client.AsyncOpenAI"):
                    with patch("nura.llm.client.get_message_adapter"):
                        with patch("nura.llm.client.format_messages") as mock_format:
                            mock_format.return_value = [{"role": "user", "content": "Hello"}]
                            llm = LLM("default")

                            messages = [{"role": "user", "content": "Hello"}]
                            llm.format_messages(messages)

                            mock_format.assert_called_once()


class TestLLMClientTokenTracking:
    """Test token tracking."""

    @pytest.fixture
    def mock_llm_config(self):
        config = MagicMock()
        config.model = "gpt-4"
        config.max_tokens = 1000
        config.temperature = 0.7
        config.api_type = "openai"
        config.api_key = "test-key"
        config.api_version = "v1"
        config.base_url = "https://api.openai.com/v1"
        config.max_input_tokens = 100000
        return config

    @pytest.mark.unit
    def test_update_token_count(self):
        """Test token count update."""
        LLM._instances = {}

        with patch("nura.llm.client.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            mock_llm_cfg = MagicMock()
            mock_llm_cfg.model = "gpt-4"
            mock_llm_cfg.max_tokens = 1000
            mock_llm_cfg.temperature = 0.7
            mock_llm_cfg.api_type = "openai"
            mock_llm_cfg.api_key = "test-key"
            mock_llm_cfg.api_version = "v1"
            mock_llm_cfg.base_url = "https://api.openai.com/v1"
            mock_llm_cfg.max_input_tokens = 100000
            mock_config.llm = {"default": mock_llm_cfg}

            with patch("nura.llm.client.tiktoken") as mock_tiktoken:
                mock_encoder = MagicMock()
                mock_encoder.encode.return_value = []
                mock_tiktoken.encoding_for_model.return_value = mock_encoder

                with patch("nura.llm.client.AsyncOpenAI"):
                    with patch("nura.llm.client.get_message_adapter"):
                        llm = LLM("default")

                        initial_input = llm.total_input_tokens
                        initial_completion = llm.total_completion_tokens

                        llm.update_token_count(100, 50)

                        assert llm.total_input_tokens == initial_input + 100
                        assert llm.total_completion_tokens == initial_completion + 50
