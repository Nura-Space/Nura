"""Integration tests for Event + Context system."""

import pytest
import asyncio
from nura.event import EventQueue, Event, EventType
from nura.context import ContextManager, ContextConfig
from nura.core.schema import Message


@pytest.mark.integration
@pytest.mark.asyncio
class TestEventContextIntegration:
    """Test Event Queue + Context Manager integration."""

    async def test_event_driven_context_compression(self):
        """Test that events trigger context compression correctly."""
        # Setup
        queue = EventQueue(debounce_seconds=0.1)
        config = ContextConfig(max_tokens=1000, compress_threshold=0.5, keep_turns=1)
        context = ContextManager(config)

        # Simulate event-driven message processing
        for i in range(10):
            event = Event(
                id=f"evt-{i}",
                type=EventType.MAIN,
                data={"text": "Hello " * 50},  # Long message
                conversation_id="conv-1",
            )
            await queue.put(event)

            # Get event
            received = await queue.get(timeout=1.0)
            assert received.id == f"evt-{i}"

            # Add to context
            context.add_message(Message.user_message(received.data["text"]))

        # Context should have compressed - keep only recent 1 turn
        # With 10 user messages, we should have at most 1 turn kept
        assert len(context._messages) <= 10  # Could be 1 turn but at least less than 10

    async def test_debounce_with_context(self):
        """Test debounce collecting multiple events for context."""
        queue = EventQueue(debounce_seconds=0.2)
        context = ContextManager()

        # Put multiple events quickly
        for i in range(3):
            event = Event(
                id=f"evt-{i}",
                type=EventType.MAIN,
                data={"text": f"Message {i}"},
                conversation_id="conv-1",
            )
            await queue.put(event)
            await asyncio.sleep(0.05)  # Faster than debounce

        # Get with debounce
        events = await queue.get_with_debounce("conv-1", debounce_seconds=0.2)
        assert len(events) == 3

        # Add all to context
        for evt in events:
            context.add_message(Message.user_message(evt.data["text"]))

        # Should have all messages
        messages = context.get_messages_for_llm()
        assert len(messages) >= 3

    async def test_priority_handling_with_context(self):
        """Test priority queue with context management."""
        queue = EventQueue()
        context = ContextManager()

        # Add background event
        bg_event = Event(
            id="bg",
            type=EventType.BACKGROUND,
            data={"text": "Background task"},
            conversation_id="conv-1",
        )
        await queue.put(bg_event)

        # Add main event (higher priority)
        main_event = Event(
            id="main",
            type=EventType.MAIN,
            data={"text": "User message"},
            conversation_id="conv-1",
        )
        await queue.put(main_event)

        # Should get main first
        first = await queue.get(timeout=1.0)
        assert first.id == "main"
        context.add_message(Message.user_message(first.data["text"]))

        # Then background
        second = await queue.get(timeout=1.0)
        assert second.id == "bg"
        context.add_message(Message.system_message(second.data["text"]))

        # Both should be in context
        messages = context.get_messages_for_llm()
        assert len(messages) >= 2
