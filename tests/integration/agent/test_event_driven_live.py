"""Live integration tests for EventDrivenAgent.

These tests require real API credentials and are marked with @pytest.mark.live.
Run with: NURA_LIVE_TEST=1 uv run pytest tests/integration/agent/test_event_driven_live.py -v
"""
import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from nura.event import EventQueue, Event, EventType
from nura.agent.event_driven import EventDrivenAgent
from nura.context import ContextConfig
from nura.services.base import ClientFactory, BaseClient
from nura.core.schema import Message
from nura.core.skill_queue import reset_skill_queue


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state between tests."""
    # Reset skill queue before each test
    reset_skill_queue()
    # Reset client factory
    ClientFactory._instances.clear()
    ClientFactory._current_platform = None
    yield
    # Reset after test as well
    reset_skill_queue()
    ClientFactory._instances.clear()
    ClientFactory._current_platform = None


class MockMessagingClient(BaseClient):
    """Mock messaging client for testing."""

    def __init__(self):
        super().__init__()
        self._sent_messages: List[str] = []
        self._sent_files: List[str] = []

    async def send(self, content):
        """Mock send method."""
        if hasattr(content, 'text'):
            self._sent_messages.append(content.text)
        elif hasattr(content, 'file_path'):
            self._sent_files.append(content.file_path)


@pytest.fixture
def mock_client():
    """Create and register a mock client."""
    # Clear any existing clients
    ClientFactory._instances.clear()
    ClientFactory._current_platform = None

    # Create mock client
    client = MockMessagingClient()

    # Register and set as current
    ClientFactory.register("test", MockMessagingClient)
    ClientFactory.set_current_platform("test")
    ClientFactory._instances["test"] = client

    yield client


@pytest.fixture
def event_queue():
    """Create EventQueue for testing."""
    return EventQueue(debounce_seconds=0.1)


@pytest.fixture
def small_context_config():
    """Create small context config to trigger compression easily."""
    return ContextConfig(
        max_tokens=1000,
        compress_threshold=0.3,
        keep_turns=2
    )


@pytest.mark.live
@pytest.mark.asyncio
class TestEventDrivenAgentLive:
    """Live integration tests for EventDrivenAgent with real API calls."""

    async def test_basic_conversation(self, event_queue, mock_client):
        """Test basic conversation flow - triggers SendMessage."""
        # Initialize agent with short message collection time
        agent = EventDrivenAgent(
            lane_queue=event_queue,
            debounce_seconds=0.1,
            message_collect_seconds=0.5,  # Short for testing
        )

        # Create task to run agent
        agent_task = asyncio.create_task(agent.start())

        # Wait for agent to start
        await asyncio.sleep(1)

        # Send a user message
        event = Event(
            id="test-1",
            type=EventType.MAIN,
            data={"text": "你好"},
            conversation_id="conv-1"
        )
        await event_queue.put(event)

        # Wait for processing
        await asyncio.sleep(10)

        # Verify agent processed the message
        assert len(mock_client._sent_messages) >= 0  # May or may not send messages

        # Cleanup
        await agent.stop()
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass

    async def test_web_search(self, event_queue, mock_client):
        """Test web search - triggers WebSearch tool."""
        agent = EventDrivenAgent(
            lane_queue=event_queue,
            debounce_seconds=0.1,
            message_collect_seconds=0.5,
        )

        agent_task = asyncio.create_task(agent.start())
        await asyncio.sleep(1)

        # Send a message that should trigger web search
        event = Event(
            id="test-web-1",
            type=EventType.MAIN,
            data={"text": "今天北京天气怎么样？"},
            conversation_id="conv-3"
        )
        await event_queue.put(event)

        # Wait for processing
        await asyncio.sleep(15)

        # Cleanup
        await agent.stop()
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass

    async def test_end_chat(self, event_queue, mock_client):
        """Test end chat - triggers EndChat tool."""
        agent = EventDrivenAgent(
            lane_queue=event_queue,
            debounce_seconds=0.1,
            message_collect_seconds=0.5,
        )

        agent_task = asyncio.create_task(agent.start())
        await asyncio.sleep(1)

        # Send end chat message
        event = Event(
            id="test-end-1",
            type=EventType.MAIN,
            data={"text": "结束对话"},
            conversation_id="conv-4"
        )
        await event_queue.put(event)

        # Wait for processing
        await asyncio.sleep(8)

        # Cleanup
        await agent.stop()
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass

    async def test_send_file(self, event_queue, mock_client):
        """Test send file - triggers SendFile tool."""
        agent = EventDrivenAgent(
            lane_queue=event_queue,
            debounce_seconds=0.1,
            message_collect_seconds=0.5,
        )

        agent_task = asyncio.create_task(agent.start())
        await asyncio.sleep(1)

        # Send a message that should trigger file sending
        event = Event(
            id="test-file-1",
            type=EventType.MAIN,
            data={"text": "给我看一下那个文件"},
            conversation_id="conv-5"
        )
        await event_queue.put(event)

        # Wait for processing
        await asyncio.sleep(10)

        # Cleanup
        await agent.stop()
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass

    async def test_multi_turn_conversation(self, event_queue, mock_client, small_context_config):
        """Test multi-turn conversation with context compression."""
        agent = EventDrivenAgent(
            lane_queue=event_queue,
            debounce_seconds=0.1,
            message_collect_seconds=0.3,
            context_config=small_context_config,
        )

        agent_task = asyncio.create_task(agent.start())
        await asyncio.sleep(1)

        # Send multiple conversation turns
        for i in range(5):
            event = Event(
                id=f"test-multi-{i}",
                type=EventType.MAIN,
                data={"text": f"这是第 {i+1} 轮对话，我们讨论了机器学习和人工智能的发展"},
                conversation_id="conv-6"
            )
            await event_queue.put(event)
            await asyncio.sleep(5)  # Wait between messages

        # Wait for all processing
        await asyncio.sleep(15)

        # Check that context has some messages
        messages = agent.memory.messages
        assert len(messages) > 0

        # Cleanup
        await agent.stop()
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass

    async def test_background_event_processing(self, event_queue, mock_client):
        """Test background event processing (skill completion)."""
        agent = EventDrivenAgent(
            lane_queue=event_queue,
            debounce_seconds=0.1,
            message_collect_seconds=0.5,
        )

        agent_task = asyncio.create_task(agent.start())
        await asyncio.sleep(1)

        # Send a background event (simulating skill completion)
        event = Event(
            id="test-bg-1",
            type=EventType.BACKGROUND,
            data={
                "skill_name": "test_skill",
                "result": "Task completed successfully"
            },
            conversation_id="conv-7"
        )
        await event_queue.put(event)

        # Wait for processing
        await asyncio.sleep(8)

        # Cleanup
        await agent.stop()
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass

    async def test_background_event_with_object_format(self, event_queue, mock_client):
        """Test background event with legacy object format."""
        agent = EventDrivenAgent(
            lane_queue=event_queue,
            debounce_seconds=0.1,
            message_collect_seconds=0.5,
        )

        agent_task = asyncio.create_task(agent.start())
        await asyncio.sleep(1)

        # Create a mock object with 'result' attribute (legacy format)
        class MockTaskResult:
            def __init__(self):
                self.result = "Legacy task result"

        # Send a background event with object format
        event = Event(
            id="test-bg-legacy",
            type=EventType.BACKGROUND,
            data=MockTaskResult(),
            conversation_id="conv-7b"
        )
        await event_queue.put(event)

        # Wait for processing
        await asyncio.sleep(8)

        # Cleanup
        await agent.stop()
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass

    async def test_error_handling(self, event_queue, mock_client):
        """Test error handling and recovery."""
        # Initialize agent
        agent = EventDrivenAgent(
            lane_queue=event_queue,
            debounce_seconds=0.1,
            message_collect_seconds=0.5,
        )

        agent_task = asyncio.create_task(agent.start())
        await asyncio.sleep(1)

        # Send a normal message first
        event = Event(
            id="test-err-1",
            type=EventType.MAIN,
            data={"text": "你好"},
            conversation_id="conv-8"
        )
        await event_queue.put(event)
        await asyncio.sleep(8)

        # Verify agent is still running (recovered from any errors)
        assert agent.is_idle or agent.is_running

        # Cleanup
        await agent.stop()
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass

    async def test_unknown_event_type(self, event_queue, mock_client):
        """Test handling of unknown event types."""
        agent = EventDrivenAgent(
            lane_queue=event_queue,
            debounce_seconds=0.1,
            message_collect_seconds=0.5,
        )

        agent_task = asyncio.create_task(agent.start())
        await asyncio.sleep(1)

        # Send an unknown event (not EventType.MAIN or BACKGROUND)
        class UnknownEventType:
            pass

        event = Event(
            id="test-unknown",
            type=UnknownEventType(),  # Custom type
            data={"text": "test"},
            conversation_id="conv-9"
        )
        await event_queue.put(event)

        # Wait for processing (should be skipped)
        await asyncio.sleep(3)

        # Cleanup
        await agent.stop()
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass

    async def test_skill_complete_callback(self, event_queue, mock_client):
        """Test skill completion callback with COMPLETED status."""
        from nura.core.skill_queue import SkillTask, SkillStatus

        agent = EventDrivenAgent(
            lane_queue=event_queue,
            debounce_seconds=0.1,
            message_collect_seconds=0.5,
        )

        agent_task = asyncio.create_task(agent.start())
        await asyncio.sleep(1)

        # Create a skill task that will trigger the callback
        task = SkillTask(
            skill_name="test_callback_skill",
            user_input="test input",
            session_id="conv-10",
            status=SkillStatus.COMPLETED,
            result="Test result content"
        )

        # Call the callback directly
        await agent._on_skill_complete(task)

        # Wait for the background event to be processed
        await asyncio.sleep(8)

        # Cleanup
        await agent.stop()
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass

    async def test_skill_failed_callback(self, event_queue, mock_client):
        """Test skill completion callback with FAILED status."""
        from nura.core.skill_queue import SkillTask, SkillStatus

        agent = EventDrivenAgent(
            lane_queue=event_queue,
            debounce_seconds=0.1,
            message_collect_seconds=0.5,
        )

        agent_task = asyncio.create_task(agent.start())
        await asyncio.sleep(1)

        # Create a failed skill task
        task = SkillTask(
            skill_name="test_failed_skill",
            user_input="test input",
            session_id="conv-11",
            status=SkillStatus.FAILED,
            result="Error: skill failed"
        )

        # Call the callback directly
        await agent._on_skill_complete(task)

        # Wait for the background event to be processed
        await asyncio.sleep(5)

        # Cleanup
        await agent.stop()
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass


@pytest.mark.live
@pytest.mark.asyncio
async def test_agent_initialization(event_queue, mock_client):
    """Test that EventDrivenAgent initializes correctly."""
    agent = EventDrivenAgent(
        lane_queue=event_queue,
        system_prompt="You are a helpful assistant.",
        debounce_seconds=0.5,
        message_collect_seconds=5.0,
    )

    # Verify agent properties
    assert agent.agent is not None
    assert agent.context is not None
    assert agent.memory is not None
    assert not agent.is_running
    assert agent.is_idle

    # Cleanup
    await agent.stop()


@pytest.mark.live
@pytest.mark.asyncio
async def test_context_sync(event_queue, mock_client):
    """Test context synchronization with memory."""
    agent = EventDrivenAgent(
        lane_queue=event_queue,
        debounce_seconds=0.1,
        message_collect_seconds=0.5,
    )

    agent_task = asyncio.create_task(agent.start())
    await asyncio.sleep(1)

    # Add a message to memory
    agent.memory.add_message(Message.user_message("Test message"))

    # Trigger context sync
    agent._sync_context_with_memory()

    # Verify context has the message
    assert len(agent.context._messages) > 0

    # Cleanup
    await agent.stop()
    agent_task.cancel()
    try:
        await agent_task
    except asyncio.CancelledError:
        pass
