"""Tests for LLM adapters."""

import pytest
from unittest.mock import MagicMock

from nura.llm.adapters.ark import ArkMessageAdapter
from nura.llm.adapters.base import BaseMessageAdapter


class TestArkMessageAdapter:
    """Test cases for ArkMessageAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create an ArkMessageAdapter instance."""
        return ArkMessageAdapter()

    @pytest.mark.unit
    def test_inherits_from_base(self, adapter):
        """Test that ArkMessageAdapter inherits from BaseMessageAdapter."""
        assert isinstance(adapter, BaseMessageAdapter)

    @pytest.mark.unit
    def test_format_for_provider_empty_messages(self, adapter):
        """Test formatting empty message list."""
        result = adapter.format_for_provider([])

        assert result == []

    @pytest.mark.unit
    def test_format_for_provider_basic_message(self, adapter):
        """Test formatting basic message."""
        messages = [{"role": "user", "content": "Hello"}]

        result = adapter.format_for_provider(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"

    @pytest.mark.unit
    def test_format_for_provider_with_dict_object(self, adapter):
        """Test formatting message with dict() method."""
        message = MagicMock()
        message.dict = MagicMock(return_value={"role": "user", "content": "Hello"})
        # Remove to_dict attribute to test dict fallback
        if hasattr(message, "to_dict"):
            delattr(message, "to_dict")

        result = adapter.format_for_provider([message])

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"

    @pytest.mark.unit
    def test_format_for_provider_with_to_dict(self, adapter):
        """Test formatting message with to_dict() method."""
        message = MagicMock()
        message.to_dict = MagicMock(
            return_value={"role": "system", "content": "You are helpful"}
        )
        message.dict = None

        result = adapter.format_for_provider([message])

        assert len(result) == 1
        assert result[0]["role"] == "system"

    @pytest.mark.unit
    def test_format_for_provider_assistant_with_tool_calls(self, adapter):
        """Test formatting assistant message with tool_calls."""
        messages = [
            {
                "role": "assistant",
                "content": "I'll help with that",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "function": {
                            "name": "search",
                            "arguments": '{"query": "test"}',
                        },
                    }
                ],
            }
        ]

        result = adapter.format_for_provider(messages)

        # Should convert tool_calls to function_call
        assert len(result) >= 1
        # Find the function_call in results
        function_calls = [r for r in result if r.get("type") == "function_call"]
        assert len(function_calls) == 1
        assert function_calls[0]["call_id"] == "call_123"
        assert function_calls[0]["name"] == "search"

    @pytest.mark.unit
    def test_format_for_provider_tool_message(self, adapter):
        """Test formatting tool message."""
        messages = [
            {
                "role": "tool",
                "content": "Search results here",
                "tool_call_id": "call_123",
            }
        ]

        result = adapter.format_for_provider(messages)

        assert len(result) == 1
        assert result[0]["type"] == "function_call_output"
        assert result[0]["call_id"] == "call_123"
        assert result[0]["output"] == "Search results here"

    @pytest.mark.unit
    def test_format_for_provider_with_tools(self, adapter):
        """Test formatting with tools parameter."""
        messages = [{"role": "user", "content": "Hello"}]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search the web",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        result = adapter.format_for_provider(messages, tools=tools)

        # Messages should remain unchanged
        assert len(result) == 1

    @pytest.mark.unit
    def test_format_for_provider_multiple_messages(self, adapter):
        """Test formatting multiple messages."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]

        result = adapter.format_for_provider(messages)

        assert len(result) == 4

    @pytest.mark.unit
    def test_format_tools_none(self, adapter):
        """Test format_tools with None."""
        result = adapter.format_tools(None)

        assert result is None

    @pytest.mark.unit
    def test_format_tools_with_tools(self, adapter):
        """Test formatting tools."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search the web",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        result = adapter.format_tools(tools)

        assert len(result) == 1
        assert result[0]["name"] == "search"
        assert result[0]["description"] == "Search the web"

    @pytest.mark.unit
    def test_format_tool_choice_string(self, adapter):
        """Test formatting tool choice as string."""
        result = adapter.format_tool_choice("auto")

        assert result == "auto"

    @pytest.mark.unit
    def test_format_tool_choice_dict(self, adapter):
        """Test formatting tool choice as dict."""
        tool_choice = {"type": "function", "function": {"name": "search"}}

        result = adapter.format_tool_choice(tool_choice)

        assert result == tool_choice

    @pytest.mark.unit
    def test_format_tool_choice_none(self, adapter):
        """Test formatting None tool choice."""
        result = adapter.format_tool_choice(None)

        assert result is None

    @pytest.mark.unit
    def test_parse_response_basic(self, adapter):
        """Test parsing basic response."""
        # Create mock response
        mock_message = MagicMock()
        mock_message.type = "message"
        mock_message.content = []

        mock_content_item = MagicMock()
        mock_content_item.type = "output_text"
        mock_content_item.text = "Hello, world!"
        mock_message.content = [mock_content_item]

        mock_response = MagicMock()
        mock_response.output = [mock_message]

        result = adapter.parse_response(mock_response)

        assert result.content == "Hello, world!"
        assert result.role == "assistant"

    @pytest.mark.unit
    def test_parse_response_with_reasoning(self, adapter):
        """Test parsing response with reasoning."""
        mock_message = MagicMock()
        mock_message.type = "message"
        mock_content = MagicMock()
        mock_content.type = "output_text"
        mock_content.text = "Final answer"
        mock_message.content = [mock_content]

        mock_reasoning = MagicMock()
        mock_reasoning.type = "reasoning"
        mock_summary = MagicMock()
        mock_summary.text = "Let me think about this..."
        mock_reasoning.summary = [mock_summary]

        mock_response = MagicMock()
        mock_response.output = [mock_reasoning, mock_message]

        result = adapter.parse_response(mock_response)

        assert result.content == "Final answer"
        assert result.reasoning_content == "Let me think about this..."

    @pytest.mark.unit
    def test_parse_response_with_tool_calls(self, adapter):
        """Test parsing response with tool calls."""
        mock_message = MagicMock()
        mock_message.type = "message"
        mock_message.content = []

        mock_function = MagicMock()
        mock_function.type = "function_call"
        mock_function.call_id = "call_123"
        mock_function.name = "search"
        mock_function.arguments = '{"query": "test"}'

        mock_response = MagicMock()
        mock_response.output = [mock_message, mock_function]

        result = adapter.parse_response(mock_response)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].id == "call_123"
        assert result.tool_calls[0].function.name == "search"

    @pytest.mark.unit
    def test_parse_response_empty_output(self, adapter):
        """Test parsing response with empty output."""
        mock_response = MagicMock()
        mock_response.output = []

        result = adapter.parse_response(mock_response)

        assert result.content == ""
        assert result.tool_calls is None

    @pytest.mark.unit
    def test_parse_response_empty_content(self, adapter):
        """Test parsing response with no text content."""
        mock_message = MagicMock()
        mock_message.type = "message"
        mock_message.content = []

        mock_response = MagicMock()
        mock_response.output = [mock_message]

        result = adapter.parse_response(mock_response)

        assert result.content == ""

    @pytest.mark.unit
    def test_parse_response_only_tool_calls(self, adapter):
        """Test parsing response with only tool calls."""
        mock_function = MagicMock()
        mock_function.type = "function_call"
        mock_function.call_id = "call_1"
        mock_function.name = "tool1"
        mock_function.arguments = "{}"

        mock_function2 = MagicMock()
        mock_function2.type = "function_call"
        mock_function2.call_id = "call_2"
        mock_function2.name = "tool2"
        mock_function2.arguments = "{}"

        mock_response = MagicMock()
        mock_response.output = [mock_function, mock_function2]

        result = adapter.parse_response(mock_response)

        assert len(result.tool_calls) == 2
