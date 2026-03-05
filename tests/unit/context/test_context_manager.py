"""Unit tests for ContextManager."""

import pytest
from nura.context import ContextManager, ContextConfig
from nura.core.schema import Message


@pytest.mark.unit
class TestContextManager:
    """Test ContextManager class."""

    def test_initialization(self):
        """Test context manager initialization."""
        manager = ContextManager()
        assert manager.token_count == 0
        assert not manager.needs_compression

    def test_add_message(self):
        """Test adding messages."""
        manager = ContextManager()
        manager.add_message(Message.user_message("Hello"))
        assert manager.token_count > 0

    @pytest.mark.asyncio
    async def test_compression_threshold(self):
        """Test compression threshold detection."""
        config = ContextConfig(
            max_tokens=100,  # Very small limit
            compress_threshold=0.5,  # 50 tokens
            keep_turns=1,  # Keep only 1 turn
            compress_cooldown=0,  # No cooldown for testing
        )
        manager = ContextManager(config)

        # Add many long messages (multiple turns)
        # Each message is about 80 chars, ~20 tokens each
        for i in range(20):
            if i % 2 == 0:
                manager.add_message(
                    Message.user_message("This is a longer message " * 20)
                )
            else:
                manager.add_message(Message.assistant_message("Response " * 20))

        # Token count should exceed threshold now
        assert manager.token_count > 50  # Should be > 50 tokens (compress threshold)
        assert manager.needs_compression

        # Manually trigger compression
        await manager.compress()

        # After compression, should have fewer messages than we added (keep only 1 turn)
        # With 10 turns and keep_turns=1, should keep only the last turn
        assert len(manager._messages) < 20

    def test_get_messages_for_llm(self):
        """Test getting messages for LLM."""
        manager = ContextManager()
        manager.add_message(Message.user_message("Hello"))
        manager.add_message(Message.assistant_message("Hi"))

        messages = manager.get_messages_for_llm()
        assert len(messages) >= 2

    def test_clear(self):
        """Test clearing context."""
        manager = ContextManager()
        manager.add_message(Message.user_message("Hello"))
        manager.clear()

        assert manager.token_count == 0
        assert len(manager._messages) == 0
