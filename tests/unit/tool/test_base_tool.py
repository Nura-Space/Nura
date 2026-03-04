"""Unit tests for BaseTool."""

import pytest
from nura.tool.base import BaseTool, ToolResult


class SampleTool(BaseTool):
    """Sample tool implementation for testing."""

    name: str = "sample_tool"
    description: str = "A sample tool"
    parameters: dict = {
        "type": "object",
        "properties": {"arg": {"type": "string"}},
        "required": ["arg"],
    }

    async def execute(self, arg: str) -> ToolResult:
        """Execute sample tool."""
        if arg == "error":
            return self.fail_response("Test error")
        return self.success_response(f"Success: {arg}")


@pytest.mark.unit
class TestBaseTool:
    """Test BaseTool class."""

    def test_tool_creation(self):
        """Test creating a tool."""
        tool = SampleTool()
        assert tool.name == "sample_tool"
        assert tool.description == "A sample tool"

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execution."""
        tool = SampleTool()
        result = await tool.execute(arg="test")
        # Success is indicated by output being set
        assert result.output is not None
        assert "Success" in result.output

    @pytest.mark.asyncio
    async def test_execute_failure(self):
        """Test failed execution."""
        tool = SampleTool()
        result = await tool.execute(arg="error")
        # Failure is indicated by error being set
        assert result.error is not None
        assert "Test error" in result.error

    def test_to_param(self):
        """Test tool to param conversion."""
        tool = SampleTool()
        tool_dict = tool.to_param()

        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "sample_tool"
        assert "parameters" in tool_dict["function"]
