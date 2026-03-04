"""Tests for event-driven agent module."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from nura.core.schema import AgentState


class MockLaneQueue:
    """Mock LaneQueue for testing."""

    def __init__(self):
        self._queue = asyncio.Queue()
        self._running = False

    async def get(self, timeout=1.0):
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def process_pending_puts(self):
        pass

    async def get_with_debounce(self, conversation_id, debounce_seconds):
        return []

    def put(self, event):
        self._queue.put_nowait(event)


def make_mock_agent():
    """Create a fully mocked EventDrivenAgent."""
    from nura.agent.event_driven import EventDrivenAgent

    # First, add MemorySearch mock to nura.tool module
    import nura.tool
    if not hasattr(nura.tool, 'MemorySearch'):
        nura.tool.MemorySearch = MagicMock(name='memory_search')

    # Now we can import and create the agent
    with patch('nura.agent.toolcall.ToolCallAgent'):
        with patch('nura.tool.collection.ToolCollection'):
            with patch('nura.context.manager.ContextManager') as mock_context:
                with patch('nura.core.skill_queue.get_skill_queue'):
                    with patch('nura.core.skill_queue.get_skill_worker'):
                        mock_context_instance = MagicMock()
                        mock_context_instance._messages = []
                        mock_context.return_value = mock_context_instance

                        lane_queue = MockLaneQueue()
                        agent = EventDrivenAgent(lane_queue=lane_queue)

    return agent


class TestEventDrivenAgent:
    """Test cases for EventDrivenAgent."""

    @pytest.mark.unit
    def test_initialization(self):
        """Test agent initialization."""
        agent = make_mock_agent()

        assert agent._lane_queue is not None
        assert agent._running is False

    @pytest.mark.unit
    def test_initialization_with_defaults(self):
        """Test initialization with default values."""
        agent = make_mock_agent()

        assert agent._debounce_seconds == 0.5
        assert agent._message_collect_seconds == 10.0

    @pytest.mark.unit
    def test_initialization_with_custom_config(self):
        """Test initialization with custom configuration."""
        from nura.agent.event_driven import EventDrivenAgent

        with patch('nura.agent.toolcall.ToolCallAgent'):
            with patch('nura.tool.collection.ToolCollection'):
                with patch('nura.context.manager.ContextManager'):
                    with patch('nura.core.skill_queue.get_skill_queue'):
                        with patch('nura.core.skill_queue.get_skill_worker'):
                            lane_queue = MockLaneQueue()
                            agent = EventDrivenAgent(
                                lane_queue=lane_queue,
                                debounce_seconds=1.0,
                                message_collect_seconds=5.0,
                            )

                            assert agent._debounce_seconds == 1.0
                            assert agent._message_collect_seconds == 5.0

    @pytest.mark.unit
    def test_agent_property(self):
        """Test the agent property returns base agent."""
        agent = make_mock_agent()

        assert agent.agent is not None

    @pytest.mark.unit
    def test_memory_property(self):
        """Test the memory property."""
        agent = make_mock_agent()

        assert agent.memory is not None

    @pytest.mark.unit
    def test_context_property(self):
        """Test the context property."""
        agent = make_mock_agent()

        assert agent.context is not None

    @pytest.mark.unit
    def test_is_running_property(self):
        """Test is_running property."""
        agent = make_mock_agent()

        agent._base_agent.state = AgentState.RUNNING
        assert agent.is_running is True

    @pytest.mark.unit
    def test_is_idle_property(self):
        """Test is_idle property."""
        agent = make_mock_agent()

        agent._base_agent.state = AgentState.IDLE
        assert agent.is_idle is True

    @pytest.mark.unit
    def test_retry_config(self):
        """Test retry configuration."""
        agent = make_mock_agent()

        assert agent._retry_config["max_retries"] == 3
        assert agent._retry_config["base_delay"] == 1.0
        assert agent._retry_config["max_delay"] == 30.0


class TestEventDrivenAgentSyncContext:
    """Test context sync functionality."""

    @pytest.mark.unit
    def test_sync_context_with_memory_empty(self):
        """Test _sync_context_with_memory with empty memory."""
        agent = make_mock_agent()

        agent.memory.messages = []
        agent._context._messages = []
        agent._sync_context_with_memory()

    @pytest.mark.unit
    def test_sync_context_with_memory_new_messages(self):
        """Test _sync_context_with_memory with new messages."""
        agent = make_mock_agent()
        agent._context._messages = [MagicMock()]

        msg1 = MagicMock()
        msg2 = MagicMock()
        # Make messages have required attributes
        type(msg1).role = "user"
        type(msg1).content = "Hello"
        type(msg2).role = "assistant"
        type(msg2).content = "Hi"
        agent.memory.messages = [msg1, msg2]

        # Mock the add_message to avoid token counting
        agent._context.add_message = MagicMock()
        agent._sync_context_with_memory()

        agent._context.add_message.assert_called()

    @pytest.mark.unit
    def test_sync_context_first_time(self):
        """Test _sync_context_with_memory when context is empty."""
        agent = make_mock_agent()
        agent._context._messages = []

        msg1 = MagicMock()
        msg2 = MagicMock()
        type(msg1).role = "user"
        type(msg1).content = "Hello"
        type(msg2).role = "assistant"
        type(msg2).content = "Hi"
        agent.memory.messages = [msg1, msg2]

        # Mock the add_message to avoid token counting
        agent._context.add_message = MagicMock()
        agent._sync_context_with_memory()

        # Should add all messages
        assert agent._context.add_message.call_count == 2


class TestEventDrivenAgentLifecycle:
    """Test agent lifecycle methods."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stop(self):
        """Test stop method."""
        agent = make_mock_agent()
        agent._running = True

        # Mock the cleanup and skill_worker
        agent._base_agent.cleanup = AsyncMock()
        agent._skill_worker.stop = AsyncMock()

        await agent.stop()

        assert agent._running is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Test start method sets running state."""
        agent = make_mock_agent()

        # Mock the skill_worker
        agent._skill_worker.start = AsyncMock()

        task = asyncio.create_task(agent.start())

        await asyncio.sleep(0.01)

        assert agent._running is True

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


class TestEventDrivenAgentProcessEvent:
    """Test event processing."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_event_invalid_type(self):
        """Test processing invalid event type."""
        agent = make_mock_agent()

        await agent._process_event("invalid")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_event_with_main_type(self):
        """Test processing MAIN event type."""
        agent = make_mock_agent()
        agent._running = False

        with patch.object(type(agent), '_handle_main_event', new_callable=AsyncMock) as mock_handler:
            from nura.event.types import Event, EventType
            mock_event = MagicMock(spec=Event)
            mock_event.type = EventType.MAIN
            mock_event.conversation_id = "test_conv"
            mock_event.data = {"text": "hello"}

            await agent._process_event(mock_event)

            mock_handler.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_event_with_background_type(self):
        """Test processing BACKGROUND event type."""
        agent = make_mock_agent()
        agent._running = False

        with patch.object(type(agent), '_handle_subagent_event', new_callable=AsyncMock) as mock_handler:
            from nura.event.types import Event, EventType
            mock_event = MagicMock(spec=Event)
            mock_event.type = EventType.BACKGROUND
            mock_event.conversation_id = "test_conv"
            mock_event.data = {"result": "done"}

            await agent._process_event(mock_event)

            mock_handler.assert_called_once()
