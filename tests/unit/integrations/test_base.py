"""Tests for nura/integrations/base.py"""

import json
import os
import pytest
import signal
import tempfile
from unittest.mock import MagicMock, patch, AsyncMock

from nura.integrations.base import BaseBot


class MockBot(BaseBot):
    """A mock implementation of BaseBot for testing."""

    def __init__(self):
        super().__init__()
        self._platform_name = "test_platform"
        self._event_handler = MagicMock()
        self._client_class = None
        self._credentials = None
        self._skill_manager = MagicMock()

    async def initialize(self, config: dict) -> None:
        """Initialize the mock bot."""
        self._config = config
        self._system_prompt = await self.build_system_prompt(config)
        self._event_queue = await self.initialize_event_queue(config)
        self._agent = await self.initialize_agent(
            config, self._event_queue, self._system_prompt
        )

    def get_event_handler(self):
        """Return mock event handler."""
        return self._event_handler

    def get_platform_name(self) -> str:
        """Return platform name."""
        return self._platform_name

    def start_platform_client(self) -> None:
        """Start mock platform client."""
        pass

    def _get_messaging_client_class(self):
        """Return mock client class."""
        return self._client_class

    def _get_platform_credentials(self, config: dict):
        """Return mock credentials."""
        return self._credentials


class TestBaseBotInitialization:
    """Unit tests for BaseBot initialization."""

    def test_initialization(self):
        """Test BaseBot initialization."""
        bot = MockBot()
        assert bot._config == {}
        assert bot._client is None
        assert bot._event_queue is None
        assert bot._agent is None
        assert bot._system_prompt == ""
        assert bot._shutdown_event is None

    def test_platform_name_property(self):
        """Test get_platform_name returns correct platform name."""
        bot = MockBot()
        assert bot.get_platform_name() == "test_platform"

    def test_event_handler_property(self):
        """Test get_event_handler returns event handler."""
        handler = MagicMock()
        bot = MockBot()
        bot._event_handler = handler
        assert bot.get_event_handler() is handler


class TestBaseBotLoadConfig:
    """Unit tests for load_config method."""

    def test_load_config_success(self):
        """Test loading config from valid JSON file."""
        bot = MockBot()
        config_data = {"test_key": "test_value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            result = bot.load_config(config_path)
            assert result == config_data
        finally:
            os.unlink(config_path)

    def test_load_config_file_not_found(self):
        """Test loading config from non-existent file."""
        bot = MockBot()
        result = bot.load_config("/non/existent/path.json")
        assert result == {}

    def test_load_config_invalid_json(self):
        """Test loading config with invalid JSON."""
        bot = MockBot()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            config_path = f.name

        try:
            result = bot.load_config(config_path)
            assert result == {}
        finally:
            os.unlink(config_path)


class TestBaseBotSetupMessagingClient:
    """Unit tests for setup_messaging_client method."""

    def setup_method(self):
        """Reset ClientFactory state before each test."""
        from nura.services.base import ClientFactory

        ClientFactory._clients = {}
        ClientFactory._instances = {}
        ClientFactory._current_platform = None

    async def test_setup_messaging_client_without_class(self):
        """Test setup_messaging_client without client class."""
        bot = MockBot()
        bot._client_class = None

        await bot.setup_messaging_client({})

        from nura.services.base import ClientFactory

        assert "test_platform" not in ClientFactory._clients

    async def test_setup_messaging_client_with_class(self):
        """Test setup_messaging_client with valid client class."""
        from nura.services.base import ClientFactory

        mock_client_class = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_class.create.return_value = mock_client_instance

        bot = MockBot()
        bot._client_class = mock_client_class
        bot._credentials = {"app_id": "test", "app_secret": "test"}

        await bot.setup_messaging_client({"test_key": "test_value"})

        assert "test_platform" in ClientFactory._clients
        assert ClientFactory._current_platform == "test_platform"


class TestBaseBotSetupTTSService:
    """Unit tests for setup_tts_service method."""

    def setup_method(self):
        """Reset ClientFactory state before each test."""
        from nura.services.base import ClientFactory

        ClientFactory._clients = {}
        ClientFactory._instances = {}
        ClientFactory._current_platform = None

    async def test_setup_tts_service_disabled(self):
        """Test setup_tts_service when voice is disabled."""
        bot = MockBot()

        await bot.setup_tts_service({"enable_voice_reply": False})

        from nura.services.base import ClientFactory

        # Should not try to get client when voice is disabled
        assert ClientFactory._instances == {}

    async def test_setup_tts_service_enabled(self):
        """Test setup_tts_service when voice is enabled."""
        from nura.services.base import ClientFactory

        mock_client = MagicMock()
        ClientFactory._clients["test_platform"] = type(mock_client)
        ClientFactory._instances["test_platform"] = mock_client

        bot = MockBot()

        await bot.setup_tts_service(
            {"enable_voice_reply": True, "tts_config": {"test": "config"}}
        )

        # Check that TTS service was called
        mock_client.set_tts_service.assert_called_once()


class TestBaseBotBuildSystemPrompt:
    """Unit tests for build_system_prompt method."""

    async def test_build_system_prompt_empty(self):
        """Test build_system_prompt with no profile and no skills."""
        mock_manager = MagicMock()
        mock_manager.build_skills_summary.return_value = ""

        with patch("nura.skill.get_skill_manager", return_value=mock_manager):
            bot = MockBot()
            result = await bot.build_system_prompt({})

            assert result == ""
            mock_manager.load_skills.assert_called_once()

    async def test_build_system_prompt_with_skills(self):
        """Test build_system_prompt with skills summary."""
        mock_manager = MagicMock()
        mock_manager.build_skills_summary.return_value = (
            "Skill1: description\nSkill2: description"
        )
        mock_manager.list_skills.return_value = ["skill1", "skill2"]

        with patch("nura.skill.get_skill_manager", return_value=mock_manager):
            bot = MockBot()
            result = await bot.build_system_prompt({})

            assert "## Available Skills" in result
            assert "Skill1" in result


class TestBaseBotInitializeEventQueue:
    """Unit tests for initialize_event_queue method."""

    async def test_initialize_event_queue(self):
        """Test initialize_event_queue creates EventQueue."""
        with patch("nura.integrations.base.EventQueue") as mock_event_queue:
            mock_queue_instance = MagicMock()
            mock_event_queue.return_value = mock_queue_instance

            bot = MockBot()
            result = await bot.initialize_event_queue({})

            mock_event_queue.assert_called_once_with(debounce_seconds=0.5)
            assert result == mock_queue_instance


class TestBaseBotInitializeAgent:
    """Unit tests for initialize_agent method."""

    async def test_initialize_agent_default_config(self):
        """Test initialize_agent with default configuration."""
        with (
            patch("nura.integrations.base.EventDrivenAgent") as mock_agent,
            patch("nura.integrations.base.ContextConfig") as mock_context_config,
        ):
            mock_queue = MagicMock()
            mock_agent_instance = MagicMock()
            mock_agent.return_value = mock_agent_instance

            bot = MockBot()
            result = await bot.initialize_agent({}, mock_queue, "test system prompt")

            mock_context_config.assert_called_once_with(
                max_tokens=128000,
                compress_threshold=0.5,
                keep_turns=10,
                compress_cooldown=60,
            )
            mock_agent.assert_called_once()
            assert result == mock_agent_instance

    async def test_initialize_agent_custom_config(self):
        """Test initialize_agent with custom configuration."""
        with (
            patch("nura.integrations.base.EventDrivenAgent") as mock_agent,
            patch("nura.integrations.base.ContextConfig"),
        ):
            mock_queue = MagicMock()
            mock_agent_instance = MagicMock()
            mock_agent.return_value = mock_agent_instance

            bot = MockBot()
            await bot.initialize_agent(
                {"message_collect_seconds": 5.0}, mock_queue, "test system prompt"
            )

            # Check that agent was called with custom message_collect_seconds
            call_kwargs = mock_agent.call_args[1]
            assert call_kwargs["message_collect_seconds"] == 5.0
            assert call_kwargs["debounce_seconds"] == 0.5


class TestBaseBotHelperMethods:
    """Unit tests for helper methods."""

    def test_get_messaging_client_class_default(self):
        """Test _get_messaging_client_class returns None by default."""
        bot = MockBot()
        assert bot._get_messaging_client_class() is None

    def test_get_platform_credentials_default(self):
        """Test _get_platform_credentials returns None by default."""
        bot = MockBot()
        assert bot._get_platform_credentials({}) is None


class TestBaseBotSignalHandlers:
    """Unit tests for signal handlers."""

    @patch("signal.signal")
    def test_setup_signal_handlers(self, mock_signal):
        """Test _setup_signal_handlers registers handlers."""
        bot = MockBot()
        bot._shutdown_event = MagicMock()

        bot._setup_signal_handlers()

        assert mock_signal.call_count == 2
        # Check SIGINT and SIGTERM are registered
        calls = mock_signal.call_args_list
        assert calls[0][0][0] == signal.SIGINT
        assert calls[1][0][0] == signal.SIGTERM


class TestBaseBotAbstractMethods:
    """Unit tests to verify abstract methods must be implemented."""

    def test_cannot_instantiate_base_bot_directly(self):
        """Test that BaseBot cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseBot()

    def test_mock_bot_can_be_instantiated(self):
        """Test that MockBot (implementing abstract methods) can be instantiated."""
        bot = MockBot()
        assert isinstance(bot, BaseBot)
        assert bot.get_platform_name() == "test_platform"


class TestBaseBotStart:
    """Unit tests for start method - skipped due to async complexity."""

    @pytest.mark.skip(reason="Complex async mocking - tested via integration tests")
    async def test_start_creates_tasks(self):
        """Test start method creates necessary tasks."""
        pass

    @pytest.mark.skip(reason="Complex async mocking - tested via integration tests")
    async def test_start_with_none_agent(self):
        """Test start method handles None agent."""
        pass


class TestBaseBotStop:
    """Unit tests for stop method."""

    async def test_stop_with_agent(self):
        """Test stop method with agent."""
        mock_agent = AsyncMock()
        bot = MockBot()
        bot._agent = mock_agent

        with pytest.raises(SystemExit):
            await bot.stop()

        mock_agent.stop.assert_called_once()

    async def test_stop_without_agent(self):
        """Test stop method without agent."""
        bot = MockBot()
        bot._agent = None

        with pytest.raises(SystemExit):
            await bot.stop()
