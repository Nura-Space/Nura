"""Integration tests for Agent + LLM system."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nura.agent.toolcall import ToolCallAgent
from nura.tool import BaseTool, ToolCollection
from nura.core.schema import AgentState
from pydantic import Field


# Define a simple test tool
class MockTool(BaseTool):
    """Mock tool for testing."""

    name: str = "mock_tool"
    description: str = "A mock tool for testing"
    parameters: dict = Field(
        default_factory=lambda: {"type": "object", "properties": {}, "required": []}
    )

    async def execute(self, **kwargs) -> str:
        return "Mock tool executed successfully"


@pytest.fixture
def mock_tool():
    """Create a mock tool for testing."""
    return MockTool()


@pytest.fixture
def mock_tool_collection(mock_tool):
    """Create a mock tool collection for testing."""
    return ToolCollection(mock_tool)


@pytest.fixture
def mock_sandbox():
    """Mock the SANDBOX_CLIENT to avoid cleanup issues."""
    mock = MagicMock()
    mock.cleanup = AsyncMock()
    return mock


@pytest.mark.integration
@pytest.mark.asyncio
class TestAgentLLMIntegration:
    """Test Agent + LLM integration with mocked LLM."""

    async def test_toolcall_agent_with_mock_llm(
        self, mock_llm, mock_tool_collection, mock_sandbox
    ):
        """Test ToolCallAgent with mocked LLM responses."""
        # Override the ask_tool to return None (no tool call)
        mock_llm.ask_tool = AsyncMock(return_value=None)

        # Patch SANDBOX_CLIENT
        with patch("nura.agent.base.SANDBOX_CLIENT", mock_sandbox):
            # Create agent with mock LLM
            agent = ToolCallAgent(
                name="test_toolcall",
                description="Test ToolCall agent",
                llm=mock_llm,
                available_tools=mock_tool_collection,
                max_steps=1,
            )

            # Run agent
            result = await agent.run("Hello")

            # Verify
            assert "Step 1" in result

    async def test_toolcall_agent_with_mock_tool_response(
        self, mock_llm, mock_tool_collection, mock_sandbox
    ):
        """Test ToolCallAgent with mocked tool call response."""
        from openai.types.chat.chat_completion_message_tool_call import (
            ChatCompletionMessageToolCall,
            Function,
        )

        mock_tool_call = ChatCompletionMessageToolCall(
            id="call_123",
            function=Function(name="mock_tool", arguments="{}"),
            type="function",
        )

        mock_message = MagicMock()
        mock_message.content = "I'll use a tool"
        mock_message.tool_calls = [mock_tool_call]

        mock_llm.ask_tool = AsyncMock(return_value=mock_message)

        with patch("nura.agent.base.SANDBOX_CLIENT", mock_sandbox):
            # Create agent
            agent = ToolCallAgent(
                name="test_tool",
                description="Test ToolCall agent",
                llm=mock_llm,
                available_tools=mock_tool_collection,
                max_steps=1,
            )

            # Run agent
            result = await agent.run("Use the mock tool")

            # Verify
            assert "Step 1" in result

    async def test_agent_state_transitions(
        self, mock_llm, mock_tool_collection, mock_sandbox
    ):
        """Test agent state transitions during execution."""
        mock_llm.ask_tool = AsyncMock(return_value=None)

        with patch("nura.agent.base.SANDBOX_CLIENT", mock_sandbox):
            agent = ToolCallAgent(
                name="test_state",
                llm=mock_llm,
                available_tools=mock_tool_collection,
                max_steps=1,
            )

            # Initial state should be IDLE
            assert agent.state == AgentState.IDLE

            # Run the agent
            await agent.run("Test")

            # After run, should be back to IDLE
            assert agent.state == AgentState.IDLE

    async def test_agent_state_context_error_handling(
        self, mock_llm, mock_tool_collection, mock_sandbox
    ):
        """Test that state_context properly handles errors."""
        mock_llm.ask_tool = AsyncMock(return_value=None)

        with patch("nura.agent.base.SANDBOX_CLIENT", mock_sandbox):
            agent = ToolCallAgent(
                name="test_error",
                llm=mock_llm,
                available_tools=mock_tool_collection,
                max_steps=1,
            )

            # Test that state_context properly handles exceptions
            with pytest.raises(ValueError):
                async with agent.state_context("invalid_state"):  # type: ignore
                    pass

            # State should be restored after error
            assert agent.state == AgentState.IDLE

    async def test_agent_memory_updates(
        self, mock_llm, mock_tool_collection, mock_sandbox
    ):
        """Test that agent memory is properly updated."""
        mock_llm.ask_tool = AsyncMock(return_value=None)

        with patch("nura.agent.base.SANDBOX_CLIENT", mock_sandbox):
            agent = ToolCallAgent(
                name="test_memory",
                llm=mock_llm,
                available_tools=mock_tool_collection,
                max_steps=1,
            )

            # Add message to memory
            agent.update_memory("user", "Hello")
            assert len(agent.messages) == 1
            assert agent.messages[0].role == "user"
            assert agent.messages[0].content == "Hello"

            # Run agent
            await agent.run()

            # Check memory has more messages
            assert len(agent.messages) >= 1

    async def test_agent_stuck_state_detection(
        self, mock_llm, mock_tool_collection, mock_sandbox
    ):
        """Test stuck state detection in agent."""
        with patch("nura.agent.base.SANDBOX_CLIENT", mock_sandbox):
            agent = ToolCallAgent(
                name="test_stuck",
                llm=mock_llm,
                available_tools=mock_tool_collection,
                max_steps=5,
                duplicate_threshold=2,
            )

            # Add duplicate assistant messages
            agent.update_memory("assistant", "Same response")
            agent.update_memory("assistant", "Same response")
            agent.update_memory("assistant", "Same response")

            # Should detect stuck state
            assert agent.is_stuck() is True

    async def test_agent_not_stuck_with_different_responses(
        self, mock_llm, mock_tool_collection, mock_sandbox
    ):
        """Test that agent is not stuck with different responses."""
        with patch("nura.agent.base.SANDBOX_CLIENT", mock_sandbox):
            agent = ToolCallAgent(
                name="test_not_stuck",
                llm=mock_llm,
                available_tools=mock_tool_collection,
                max_steps=5,
            )

            # Add different assistant messages
            agent.update_memory("assistant", "Response 1")
            agent.update_memory("assistant", "Response 2")
            agent.update_memory("assistant", "Response 3")

            # Should not detect stuck state
            assert agent.is_stuck() is False


@pytest.mark.live
@pytest.mark.integration
@pytest.mark.asyncio
class TestAgentWithRealLLM:
    """Test Agent with real LLM API calls.

    These tests require NURA_LIVE_TEST=1 to run.
    """

    @pytest.mark.skip(
        reason="Requires real LLM API connection - network is unreliable in test environment"
    )
    async def test_toolcall_agent_with_real_llm(self, real_llm):
        """Test ToolCallAgent with real LLM API call."""
        # Define a simple tool
        tools = ToolCollection(MockTool())

        # Mock sandbox client
        mock_sandbox = MagicMock()
        mock_sandbox.cleanup = AsyncMock()

        with patch("nura.agent.base.SANDBOX_CLIENT", mock_sandbox):
            agent = ToolCallAgent(
                name="live_toolcall",
                description="Live test ToolCall agent",
                llm=real_llm,
                available_tools=tools,
                max_steps=1,
                system_prompt="You are a helpful assistant that uses tools when needed. Keep responses brief.",
            )

            # Run with a simple request
            result = await agent.run("Hello, say hi")

            # Verify
            assert result is not None
            assert "Step 1" in result

    @pytest.mark.skip(
        reason="Requires real LLM API connection - network is unreliable in test environment"
    )
    async def test_agent_token_tracking(self, real_llm):
        """Test that agent tracks token usage from LLM."""
        # Reset token counts
        real_llm.total_input_tokens = 0
        real_llm.total_completion_tokens = 0

        tools = ToolCollection(MockTool())

        # Mock sandbox client
        mock_sandbox = MagicMock()
        mock_sandbox.cleanup = AsyncMock()

        with patch("nura.agent.base.SANDBOX_CLIENT", mock_sandbox):
            agent = ToolCallAgent(
                name="live_tokens",
                llm=real_llm,
                available_tools=tools,
                max_steps=1,
                system_prompt="You are a helpful assistant. Keep responses brief.",
            )

            # Run agent
            await agent.run("Say exactly 'test'.")

            # Token counts should be updated
            # Note: Actual values depend on API response
            assert (
                real_llm.total_input_tokens > 0 or real_llm.total_completion_tokens > 0
            )
