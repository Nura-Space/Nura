"""Unit tests for schema module."""
import pytest
from nura.core.schema import Message, Memory, AgentState


@pytest.mark.unit
class TestMessage:
    """Test Message class."""

    def test_user_message_creation(self):
        """Test creating user message."""
        msg = Message.user_message("Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_assistant_message_creation(self):
        """Test creating assistant message."""
        msg = Message.assistant_message("Hi there")
        assert msg.role == "assistant"
        assert msg.content == "Hi there"

    def test_system_message_creation(self):
        """Test creating system message."""
        msg = Message.system_message("System prompt")
        assert msg.role == "system"
        assert msg.content == "System prompt"

    def test_message_add_list(self):
        """Test Message + list operation."""
        msg = Message.user_message("Hello")
        other_msg1 = Message.assistant_message("msg1")
        other_msg2 = Message.system_message("msg2")
        result = msg + [other_msg1, other_msg2]
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == msg
        assert result[1] == other_msg1

    def test_message_add_message(self):
        """Test Message + Message operation."""
        msg1 = Message.user_message("Hello")
        msg2 = Message.assistant_message("Hi")
        result = msg1 + msg2
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == msg1
        assert result[1] == msg2

    def test_message_add_invalid_type(self):
        """Test Message + invalid type raises TypeError."""
        msg = Message.user_message("Hello")
        with pytest.raises(TypeError):
            _ = msg + "invalid"

    def test_radd_list(self):
        """Test list + Message operation."""
        msg = Message.user_message("Hello")
        other_msg1 = Message.assistant_message("msg1")
        other_msg2 = Message.system_message("msg2")
        result = [other_msg1, other_msg2] + msg
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == other_msg1
        assert result[2] == msg

    def test_radd_invalid_type(self):
        """Test invalid type + Message raises TypeError."""
        msg = Message.user_message("Hello")
        with pytest.raises(TypeError):
            _ = "invalid" + msg

    def test_message_to_dict(self):
        """Test Message.to_dict method."""
        msg = Message(role="user", content="Hello")
        d = msg.to_dict()
        assert d == {"role": "user", "content": "Hello"}

    def test_message_to_dict_with_optional_fields(self):
        """Test Message.to_dict with optional fields."""
        msg = Message(
            role="user",
            content="Hello",
            name="test_name",
            tool_call_id="call_123",
            base64_image="abc123"
        )
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "Hello"
        assert d["name"] == "test_name"
        assert d["tool_call_id"] == "call_123"
        assert d["base64_image"] == "abc123"

    def test_message_to_dict_with_tool_calls(self):
        """Test Message.to_dict with tool_calls."""
        msg = Message(
            role="assistant",
            content="Using tool",
            tool_calls=[{"id": "call_1", "type": "function", "function": {"name": "test", "arguments": "{}"}}]
        )
        d = msg.to_dict()
        assert "tool_calls" in d
        assert d["tool_calls"][0]["id"] == "call_1"


@pytest.mark.unit
class TestMemory:
    """Test Memory class."""

    def test_add_message(self):
        """Test adding messages to memory."""
        memory = Memory(max_messages=3)
        memory.add_message(Message.user_message("1"))
        memory.add_message(Message.user_message("2"))

        assert len(memory.messages) == 2

    def test_max_messages_limit(self):
        """Test max messages enforcement."""
        memory = Memory(max_messages=2)
        memory.add_message(Message.user_message("1"))
        memory.add_message(Message.user_message("2"))
        memory.add_message(Message.user_message("3"))

        assert len(memory.messages) == 2

    def test_memory_clear(self):
        """Test clearing memory."""
        memory = Memory(max_messages=10)
        memory.add_message(Message.user_message("1"))
        memory.add_message(Message.user_message("2"))
        memory.clear()
        assert len(memory.messages) == 0


@pytest.mark.unit
class TestAgentState:
    """Test AgentState enum."""

    def test_agent_states(self):
        """Test all agent states."""
        assert AgentState.IDLE == "IDLE"
        assert AgentState.RUNNING == "RUNNING"
        assert AgentState.FINISHED == "FINISHED"
        assert AgentState.ERROR == "ERROR"
