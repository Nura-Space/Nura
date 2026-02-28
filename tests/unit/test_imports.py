"""Test that all core modules can be imported."""
import pytest


@pytest.mark.unit
class TestImports:
    """Test module imports."""

    def test_core_imports(self):
        """Test core module imports."""
        from nura.core.schema import Message, Memory, AgentState
        from nura.core.exceptions import ToolError, TokenLimitExceeded
        from nura.core.logger import logger
        from nura.core.config import config
        from nura.core.cache import CacheManager

    def test_event_imports(self):
        """Test event module imports."""
        from nura.event import Event, EventType, EventQueue

    def test_context_imports(self):
        """Test context module imports."""
        from nura.context import ContextConfig, ContextManager

    def test_service_imports(self):
        """Test service module imports."""
        from nura.services import MessagingService, TTSService

    def test_agent_imports(self):
        """Test agent module imports."""
        from nura.agent.base import BaseAgent
        from nura.agent.toolcall import ToolCallAgent

    def test_tool_imports(self):
        """Test tool module imports."""
        from nura.tool.base import BaseTool, ToolResult
        from nura.tool.collection import ToolCollection

    def test_top_level_imports(self):
        """Test top-level package imports."""
        import nura
        assert nura.__version__ == "0.1.0"

        # Test that key classes are available
        from nura import Message, EventQueue, ContextManager, MessagingService
