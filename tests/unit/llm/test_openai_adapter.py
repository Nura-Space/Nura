"""Tests for openai adapter."""
import pytest
from unittest.mock import MagicMock

from nura.llm.adapters.openai import OpenAIMessageAdapter


class TestOpenAIMessageAdapter:
    """Test cases for OpenAIMessageAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create an OpenAIMessageAdapter instance."""
        return OpenAIMessageAdapter()

    @pytest.mark.unit
    def test_format_for_provider_empty(self, adapter):
        """Test formatting empty message list."""
        result = adapter.format_for_provider([])
        assert result == []

    @pytest.mark.unit
    def test_format_for_provider_basic(self, adapter):
        """Test formatting basic message."""
        messages = [{"role": "user", "content": "Hello"}]
        result = adapter.format_for_provider(messages)
        assert len(result) == 1

    @pytest.mark.unit
    def test_format_for_provider_with_object_to_dict(self, adapter):
        """Test formatting message with to_dict method."""
        message = MagicMock()
        message.to_dict.return_value = {"role": "user", "content": "Hello"}
        message.dict = None

        result = adapter.format_for_provider([message])
        assert len(result) == 1

    @pytest.mark.unit
    def test_format_for_provider_with_object_dict(self, adapter):
        """Test formatting message with dict method."""
        message = MagicMock()
        message.dict.return_value = {"role": "user", "content": "Hello"}

        result = adapter.format_for_provider([message])
        assert len(result) == 1

    @pytest.mark.unit
    def test_format_for_provider_with_tools(self, adapter):
        """Test formatting with tools."""
        messages = [{"role": "user", "content": "Hello"}]
        tools = [{"type": "function", "function": {"name": "test"}}]

        result = adapter.format_for_provider(messages, tools=tools)
        assert len(result) == 1

    @pytest.mark.unit
    def test_format_for_provider_with_tool_choice(self, adapter):
        """Test formatting with tool choice."""
        messages = [{"role": "user", "content": "Hello"}]
        tool_choice = "auto"

        result = adapter.format_for_provider(messages, tool_choice=tool_choice)
        assert len(result) == 1

    @pytest.mark.unit
    def test_format_tools_none(self, adapter):
        """Test format_tools with None."""
        result = adapter.format_tools(None)
        assert result is None

    @pytest.mark.unit
    def test_format_tools_with_tools(self, adapter):
        """Test format_tools with tools."""
        tools = [{"type": "function", "function": {"name": "test", "description": "A test tool"}}]
        result = adapter.format_tools(tools)
        assert result == tools

    @pytest.mark.unit
    def test_format_tool_choice_none(self, adapter):
        """Test format_tool_choice with None."""
        result = adapter.format_tool_choice(None)
        assert result is None

    @pytest.mark.unit
    def test_format_tool_choice_string(self, adapter):
        """Test format_tool_choice with string."""
        result = adapter.format_tool_choice("auto")
        assert result == "auto"

    @pytest.mark.unit
    def test_format_tool_choice_dict(self, adapter):
        """Test format_tool_choice with dict."""
        tool_choice = {"type": "function", "function": {"name": "test"}}
        result = adapter.format_tool_choice(tool_choice)
        assert result == tool_choice

    @pytest.mark.unit
    def test_parse_response_basic(self, adapter):
        """Test parse_response with basic message."""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello"
        mock_choice.message.tool_calls = None
        mock_response.choices = [mock_choice]

        result = adapter.parse_response(mock_response)
        assert result.content == "Hello"

    @pytest.mark.unit
    def test_parse_response_with_tool_calls(self, adapter):
        """Test parse_response with tool calls."""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = None

        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "test"
        mock_tool_call.function.arguments = "{}"

        mock_choice.message.tool_calls = [mock_tool_call]
        mock_response.choices = [mock_choice]

        result = adapter.parse_response(mock_response)
        assert len(result.tool_calls) == 1
