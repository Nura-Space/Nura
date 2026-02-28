"""Tests for LLM message formatting."""
import pytest

from nura.llm import LLM
from nura.core.schema import Message


class TestMessageFormatting:
    """Test suite for LLM.format_messages method."""

    # === Basic message formatting ===

    def test_format_messages_basic(self):
        """Test basic message formatting with dicts."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]
        formatted = LLM.format_messages(messages)
        assert len(formatted) == 2
        assert formatted[0]["role"] == "system"
        assert formatted[1]["role"] == "user"

    def test_format_messages_with_message_objects(self):
        """Test formatting with Message objects."""
        messages = [
            Message.system_message("You are helpful."),
            Message.user_message("Hello"),
        ]
        formatted = LLM.format_messages(messages)
        assert len(formatted) == 2
        assert formatted[0]["role"] == "system"
        assert formatted[1]["role"] == "user"

    def test_format_messages_mixed_types(self):
        """Test formatting with mixed dict and Message objects."""
        messages = [
            Message.system_message("You are helpful."),
            {"role": "user", "content": "Hello"},
        ]
        formatted = LLM.format_messages(messages)
        assert len(formatted) == 2

    def test_format_messages_with_assistant_message(self):
        """Test formatting with assistant message."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        formatted = LLM.format_messages(messages)
        assert len(formatted) == 3
        assert formatted[2]["role"] == "assistant"

    def test_format_messages_with_tool_message(self):
        """Test formatting with tool message."""
        messages = [
            {"role": "user", "content": "What's the weather?"},
            {
                "role": "tool",
                "tool_call_id": "call_123",
                "content": "Sunny, 25°C"
            },
        ]
        formatted = LLM.format_messages(messages)
        assert len(formatted) == 2

    # === Image handling ===

    def test_format_messages_with_images(self):
        """Test formatting messages with base64 images when supported."""
        messages = [
            {
                "role": "user",
                "content": "What's in this image?",
                "base64_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            },
        ]
        formatted = LLM.format_messages(messages, supports_images=True)
        assert len(formatted) == 1
        assert "base64_image" not in formatted[0]
        assert "content" in formatted[0]
        assert isinstance(formatted[0]["content"], list)

    def test_format_messages_with_images_not_supported(self):
        """Test that base64_image is removed when images not supported."""
        messages = [
            {
                "role": "user",
                "content": "What's in this image?",
                "base64_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            },
        ]
        formatted = LLM.format_messages(messages, supports_images=False)
        assert len(formatted) == 1
        assert "base64_image" not in formatted[0]
        assert formatted[0]["content"] == "What's in this image?"

    def test_format_messages_image_content_string(self):
        """Test formatting with base64_image and string content."""
        messages = [
            {
                "role": "user",
                "content": "Describe this",
                "base64_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            },
        ]
        formatted = LLM.format_messages(messages, supports_images=True)
        assert len(formatted) == 1
        assert isinstance(formatted[0]["content"], list)
        # Should have text and image_url items
        content_types = [item.get("type") for item in formatted[0]["content"]]
        assert "text" in content_types
        assert "image_url" in content_types

    def test_format_messages_image_content_list(self):
        """Test formatting with base64_image and list content."""
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": "Describe this"}],
                "base64_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            },
        ]
        formatted = LLM.format_messages(messages, supports_images=True)
        assert len(formatted) == 1
        content_types = [item.get("type") for item in formatted[0]["content"]]
        assert "text" in content_types
        assert "image_url" in content_types

    # === Validation and error handling ===

    def test_format_messages_invalid_role(self):
        """Test that invalid role raises ValueError."""
        messages = [
            {"role": "invalid_role", "content": "Hello"},
        ]
        with pytest.raises(ValueError, match="Invalid role"):
            LLM.format_messages(messages)

    def test_format_messages_missing_role_dict(self):
        """Test that missing role in dict raises ValueError."""
        messages = [
            {"content": "Hello"},
        ]
        with pytest.raises(ValueError, match="Message dict must contain 'role' field"):
            LLM.format_messages(messages)

    def test_format_messages_invalid_type(self):
        """Test that invalid message type raises TypeError."""
        messages = [
            "invalid message",
        ]
        with pytest.raises(TypeError, match="Unsupported message type"):
            LLM.format_messages(messages)

    def test_format_messages_no_content(self):
        """Test that messages without content are filtered out."""
        messages = [
            {"role": "system"},  # No content
            {"role": "user", "content": "Hello"},
        ]
        formatted = LLM.format_messages(messages)
        # Should only include the message with content
        assert len(formatted) == 1
        assert formatted[0]["role"] == "user"

    def test_format_messages_with_tool_calls(self):
        """Test formatting messages with tool_calls."""
        messages = [
            {
                "role": "assistant",
                "content": "I'll check the weather.",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"city": "Beijing"}'
                        }
                    }
                ]
            }
        ]
        formatted = LLM.format_messages(messages)
        assert len(formatted) == 1
        assert "tool_calls" in formatted[0]

    # === Edge cases ===

    def test_format_messages_empty_list(self):
        """Test formatting empty message list."""
        formatted = LLM.format_messages([])
        assert formatted == []

    def test_format_messages_only_system(self):
        """Test formatting with only system message."""
        messages = [
            {"role": "system", "content": "You are helpful."},
        ]
        formatted = LLM.format_messages(messages)
        assert len(formatted) == 1

    def test_format_messages_strips_empty_content(self):
        """Test that messages with empty content are handled correctly."""
        messages = [
            {"role": "system", "content": ""},
            {"role": "user", "content": "Hello"},
        ]
        formatted = LLM.format_messages(messages)
        # Empty content should be included but count as 0 tokens
        assert len(formatted) >= 1
