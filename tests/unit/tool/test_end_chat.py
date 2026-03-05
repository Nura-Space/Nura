"""Unit tests for EndChat tool."""

import pytest

from nura.tool.end_chat import EndChat


@pytest.mark.unit
class TestEndChat:
    """Test EndChat tool."""

    def test_end_chat_creation(self):
        """Test creating an EndChat tool."""
        tool = EndChat()
        assert tool.name == "end_chat"
        assert "end" in tool.description.lower()
        assert "chat" in tool.description.lower()

    def test_end_chat_parameters(self):
        """Test EndChat parameters schema."""
        tool = EndChat()
        params = tool.parameters

        assert params["type"] == "object"
        # reason is optional
        assert "reason" in params["properties"]
        assert "required" in params
        assert len(params["required"]) == 0

    @pytest.mark.asyncio
    async def test_execute_without_reason(self):
        """Test execute without reason parameter."""
        tool = EndChat()
        result = await tool.execute()

        assert result.output is not None
        assert "ended" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_with_reason(self):
        """Test execute with reason parameter."""
        tool = EndChat()
        result = await tool.execute(reason="user said goodbye")

        assert result.output is not None
        assert "ended" in result.output.lower()
        assert "user said goodbye" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_with_empty_reason(self):
        """Test execute with empty string reason."""
        tool = EndChat()
        result = await tool.execute(reason="")

        # Empty reason should still work
        assert result.output is not None

    def test_to_param(self):
        """Test tool to param conversion."""
        tool = EndChat()
        tool_dict = tool.to_param()

        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "end_chat"
        assert "parameters" in tool_dict["function"]
