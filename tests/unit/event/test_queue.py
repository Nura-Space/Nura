"""Unit tests for EventQueue."""
import pytest
import asyncio
from nura.event import EventQueue, Event, EventType


@pytest.mark.unit
@pytest.mark.asyncio
class TestEventQueue:
    """Test EventQueue class."""

    async def test_put_and_get(self):
        """Test basic put/get operations."""
        queue = EventQueue()
        event = Event(
            id="test-1",
            type=EventType.MAIN,
            data="test data",
            conversation_id="conv-1"
        )

        await queue.put(event)
        retrieved = await queue.get(timeout=1.0)

        assert retrieved.id == "test-1"
        assert retrieved.data == "test data"

    async def test_priority_main_over_background(self):
        """Test MAIN events have priority over BACKGROUND."""
        queue = EventQueue()

        # Put BACKGROUND first, then MAIN
        bg_event = Event(id="bg", type=EventType.BACKGROUND, data="bg", conversation_id="c1")
        main_event = Event(id="main", type=EventType.MAIN, data="main", conversation_id="c1")

        await queue.put(bg_event)
        await queue.put(main_event)

        # Should get MAIN first
        first = await queue.get(timeout=1.0)
        assert first.id == "main"

        second = await queue.get(timeout=1.0)
        assert second.id == "bg"

    async def test_timeout(self):
        """Test get with timeout returns None."""
        queue = EventQueue()
        result = await queue.get(timeout=0.1)
        assert result is None

    async def test_debounce(self):
        """Test debounce collects multiple events."""
        queue = EventQueue(debounce_seconds=0.2)
        conv_id = "conv-1"

        # Put multiple events quickly
        for i in range(3):
            event = Event(id=f"e{i}", type=EventType.MAIN, data=f"data{i}", conversation_id=conv_id)
            await queue.put(event)
            await asyncio.sleep(0.05)  # Shorter than debounce

        # Get with debounce should collect all
        events = await queue.get_with_debounce(conv_id, debounce_seconds=0.2)
        assert len(events) == 3

    async def test_initialization_default(self):
        """Test EventQueue initialization with defaults."""
        queue = EventQueue()
        # Check debounce_seconds is set
        assert queue._debounce_seconds == 0.5

    async def test_initialization_custom_debounce(self):
        """Test EventQueue initialization with custom debounce."""
        queue = EventQueue(debounce_seconds=1.0)
        assert queue._debounce_seconds == 1.0

    async def test_empty_both_queues_empty(self):
        """Test empty() returns True when both queues are empty."""
        queue = EventQueue()
        assert queue.empty() is True

    async def test_empty_false_when_main_has_event(self):
        """Test empty() returns False when main queue has event."""
        queue = EventQueue()
        event = Event(type=EventType.MAIN, data="test", conversation_id="conv1", id="e1")
        await queue.put(event)
        assert queue.empty() is False

    async def test_empty_false_when_background_has_event(self):
        """Test empty() returns False when background queue has event."""
        queue = EventQueue()
        event = Event(type=EventType.BACKGROUND, data="test", conversation_id="conv1", id="e1")
        await queue.put(event)
        assert queue.empty() is False

    def test_main_empty_true_when_empty(self):
        """Test main_empty() returns True when main queue is empty."""
        queue = EventQueue()
        assert queue.main_empty() is True

    def test_lane_queue_property(self):
        """Test lane_queue property returns main queue."""
        queue = EventQueue()
        assert queue.lane_queue is queue._main_queue

    async def test_qsize_returns_dict(self):
        """Test qsize returns correct dict format."""
        queue = EventQueue()
        sizes = queue.qsize()
        assert isinstance(sizes, dict)
        assert EventType.MAIN in sizes
        assert EventType.BACKGROUND in sizes

    async def test_process_pending_puts_empty(self):
        """Test process_pending_puts with no pending puts."""
        queue = EventQueue()
        count = await queue.process_pending_puts()
        assert count == 0

    async def test_process_pending_puts_with_pending(self):
        """Test process_pending_puts processes pending events."""
        queue = EventQueue()
        event = Event(type=EventType.MAIN, data="test", conversation_id="conv1", id="e1")
        queue.put_thread_safe(event)

        count = await queue.process_pending_puts()
        assert count == 1

        # Verify event was moved to queue
        result = await queue.get(timeout=1.0)
        assert result.data == "test"

    async def test_get_with_debounce_single_event(self):
        """Test get_with_debounce with single event."""
        queue = EventQueue()
        event = Event(type=EventType.MAIN, data="test", conversation_id="conv1", id="e1")
        await queue.put(event)

        events = await queue.get_with_debounce("conv1", debounce_seconds=0.1)
        assert len(events) == 1
        assert events[0].data == "test"

    async def test_get_with_debounce_multiple_events_same_conversation(self):
        """Test get_with_debounce with multiple events same conversation."""
        queue = EventQueue()
        conv_id = "conv1"

        # Put multiple events
        event1 = Event(type=EventType.MAIN, data="test1", conversation_id=conv_id, id="e1")
        event2 = Event(type=EventType.MAIN, data="test2", conversation_id=conv_id, id="e2")
        await queue.put(event1)
        await queue.put(event2)

        events = await queue.get_with_debounce(conv_id, debounce_seconds=0.1)
        assert len(events) == 2

    async def test_get_with_debounce_different_conversation(self):
        """Test get_with_debounce stops at different conversation."""
        queue = EventQueue()

        event1 = Event(type=EventType.MAIN, data="test1", conversation_id="conv1", id="e1")
        event2 = Event(type=EventType.MAIN, data="test2", conversation_id="conv2", id="e2")
        await queue.put(event1)
        await queue.put(event2)

        events = await queue.get_with_debounce("conv1", debounce_seconds=0.05)
        # Should only get conv1 events
        assert len(events) == 1
        assert events[0].conversation_id == "conv1"

    async def test_get_with_debounce_timeout_returns_events(self):
        """Test get_with_debounce returns events on timeout."""
        queue = EventQueue(debounce_seconds=0.1)
        event = Event(type=EventType.MAIN, data="test", conversation_id="conv1", id="e1")
        await queue.put(event)

        events = await queue.get_with_debounce("conv1", debounce_seconds=0.1)
        assert len(events) == 1

    async def test_get_background_event(self):
        """Test getting BACKGROUND event."""
        queue = EventQueue()
        event = Event(type=EventType.BACKGROUND, data="bg", conversation_id="conv1", id="e1")
        await queue.put(event)

        result = await queue.get(timeout=1.0)
        assert result.type == EventType.BACKGROUND
        assert result.data == "bg"

    async def test_put_thread_safe_main(self):
        """Test thread-safe put for MAIN events."""
        queue = EventQueue()
        event = Event(type=EventType.MAIN, data="test", conversation_id="conv1", id="e1")
        queue.put_thread_safe(event)

        # Process pending
        count = await queue.process_pending_puts()
        assert count == 1

    async def test_put_thread_safe_background(self):
        """Test thread-safe put for BACKGROUND events."""
        queue = EventQueue()
        event = Event(type=EventType.BACKGROUND, data="test", conversation_id="conv1", id="e1")
        queue.put_thread_safe(event)

        # Process pending
        count = await queue.process_pending_puts()
        assert count == 1


@pytest.mark.unit
class TestEvent:
    """Unit tests for Event class."""

    def test_event_creation_main(self):
        """Test creating a MAIN event."""
        event = Event(id="e1", type=EventType.MAIN, data="test", conversation_id="conv1")
        assert event.type == EventType.MAIN
        assert event.data == "test"
        assert event.id == "e1"
        assert event.conversation_id == "conv1"

    def test_event_creation_background(self):
        """Test creating a BACKGROUND event."""
        event = Event(id="e1", type=EventType.BACKGROUND, data="test", conversation_id="conv1")
        assert event.type == EventType.BACKGROUND
        assert event.data == "test"

    def test_event_timestamp_default(self):
        """Test event has timestamp by default."""
        import time
        event = Event(id="e1", type=EventType.MAIN, data="test", conversation_id="conv1")
        # Timestamp should be close to current time
        assert abs(event.timestamp - time.time()) < 1

    def test_event_with_custom_timestamp(self):
        """Test event with custom timestamp."""
        event = Event(id="e1", type=EventType.MAIN, data="test", conversation_id="conv1", timestamp=1234567890.0)
        assert event.timestamp == 1234567890.0
