"""Tests for nura/context/ modules"""

from nura.context.config import ContextConfig
from nura.context.manager import ContextManager
from nura.core.schema import Message


class TestContextConfig:
    """Unit tests for ContextConfig."""

    def test_default_values(self):
        """Test ContextConfig default values."""
        config = ContextConfig()
        assert config.max_tokens == 128000
        assert config.compress_threshold == 0.5
        assert config.keep_turns == 10
        assert config.compress_cooldown == 60

    def test_custom_values(self):
        """Test ContextConfig with custom values."""
        config = ContextConfig(
            max_tokens=64000,
            compress_threshold=0.6,
            keep_turns=5,
            compress_cooldown=30
        )
        assert config.max_tokens == 64000
        assert config.compress_threshold == 0.6
        assert config.keep_turns == 5
        assert config.compress_cooldown == 30

    def test_compress_tokens_property(self):
        """Test compress_tokens computed property."""
        config = ContextConfig(max_tokens=1000, compress_threshold=0.5)
        assert config.compress_tokens == 500

    def test_compress_tokens_different_threshold(self):
        """Test compress_tokens with different threshold."""
        config = ContextConfig(max_tokens=1000, compress_threshold=0.8)
        assert config.compress_tokens == 800


class TestContextManager:
    """Unit tests for ContextManager."""

    def test_initialization_default(self):
        """Test ContextManager initialization with defaults."""
        manager = ContextManager()
        assert manager.config.max_tokens == 128000
        assert len(manager._messages) == 0
        assert manager._summary is None

    def test_initialization_custom_config(self):
        """Test ContextManager initialization with custom config."""
        config = ContextConfig(max_tokens=64000)
        manager = ContextManager(config=config)
        assert manager.config.max_tokens == 64000

    def test_add_message(self):
        """Test adding messages to context."""
        manager = ContextManager()
        msg = Message.user_message("Hello")
        manager.add_message(msg)
        assert len(manager._messages) == 1

    def test_get_messages_empty(self):
        """Test getting messages when empty."""
        manager = ContextManager()
        messages = manager.get_messages()
        assert messages == []

    def test_get_messages_with_content(self):
        """Test getting messages with content."""
        manager = ContextManager()
        msg = Message.user_message("Hello")
        manager.add_message(msg)
        messages = manager.get_messages()
        assert len(messages) == 1
        assert messages[0].content == "Hello"

    def test_clear(self):
        """Test clearing context."""
        manager = ContextManager()
        manager.add_message(Message.user_message("Hello"))
        manager.add_message(Message.assistant_message("Hi"))
        manager.clear()
        assert len(manager._messages) == 0
        assert manager._summary is None

    def test_get_messages_for_llm_empty(self):
        """Test get_messages_for_llm when empty."""
        manager = ContextManager()
        messages = manager.get_messages_for_llm()
        assert messages == []

    def test_get_messages_for_llm_with_messages(self):
        """Test get_messages_for_llm with messages."""
        manager = ContextManager()
        manager.add_message(Message.user_message("Hello"))
        manager.add_message(Message.assistant_message("Hi there"))
        messages = manager.get_messages_for_llm()
        assert len(messages) == 2

    def test_token_counting_fallback(self):
        """Test token counting with fallback estimator."""
        manager = ContextManager()
        # Without tokenizer, should use fallback
        count = manager._count_tokens("hello world")
        # 11 chars / 4 = 2 tokens (integer division)
        assert count == 2

    def test_estimate_tokens_simple(self):
        """Test _estimate_tokens_simple."""
        manager = ContextManager()
        assert manager._estimate_tokens_simple("") == 0
        assert manager._estimate_tokens_simple("abcd") == 1
        assert manager._estimate_tokens_simple("abcdefgh") == 2

    def test_count_message_tokens(self):
        """Test _count_message_tokens."""
        manager = ContextManager()
        msg = Message(role="user", content="Hello")
        count = manager._count_message_tokens(msg)
        # Base 4 + content tokens
        assert count >= 4
