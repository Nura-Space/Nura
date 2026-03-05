"""Tests for nura/tool/collection.py"""

import pytest
from typing import Any, Optional

from nura.tool.collection import ToolCollection
from nura.tool.base import ToolResult, ToolFailure
from nura.core.exceptions import ToolError


class MockTool:
    """A mock tool for testing."""

    name: str = "mock_tool"
    description: str = "A mock tool for testing"
    parameters: Optional[dict] = None

    def __init__(self, should_fail: bool = False, error_message: str = "Tool error"):
        self.should_fail = should_fail
        self.error_message = error_message
        self.was_called = False
        self.call_args = None

    async def execute(self, **kwargs) -> ToolResult:
        self.was_called = True
        self.call_args = kwargs
        if self.should_fail:
            raise ToolError(self.error_message)
        return self._success_response(f"Executed with {kwargs}")

    def to_param(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def _success_response(self, data: Any) -> ToolResult:
        return ToolResult(output=data)

    def __call__(self, **kwargs) -> ToolResult:
        return self.execute(**kwargs)


class AnotherMockTool:
    """Another mock tool for testing."""

    name: str = "another_tool"
    description: str = "Another mock tool"
    parameters: Optional[dict] = None

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(output="Another tool executed")

    def to_param(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def __call__(self, **kwargs) -> ToolResult:
        return self.execute(**kwargs)


class TestToolCollection:
    """Unit tests for ToolCollection."""

    def test_initialization_with_tools(self):
        """Test ToolCollection initialization with tools."""
        tool1 = MockTool()
        tool2 = AnotherMockTool()
        collection = ToolCollection(tool1, tool2)

        assert len(collection.tools) == 2
        assert collection.tool_map["mock_tool"] is tool1
        assert collection.tool_map["another_tool"] is tool2

    def test_initialization_empty(self):
        """Test ToolCollection initialization with no tools."""
        collection = ToolCollection()
        assert len(collection.tools) == 0
        assert len(collection.tool_map) == 0

    def test_iter(self):
        """Test that ToolCollection is iterable."""
        tool1 = MockTool()
        tool2 = AnotherMockTool()
        collection = ToolCollection(tool1, tool2)

        tools_list = list(collection)
        assert len(tools_list) == 2
        assert tools_list[0] is tool1
        assert tools_list[1] is tool2

    def test_to_params(self):
        """Test to_params returns correct format."""
        tool1 = MockTool()
        tool2 = AnotherMockTool()
        collection = ToolCollection(tool1, tool2)

        params = collection.to_params()
        assert len(params) == 2
        assert params[0]["type"] == "function"
        assert params[0]["function"]["name"] == "mock_tool"
        assert params[1]["function"]["name"] == "another_tool"

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test execute returns success result."""
        tool = MockTool()
        collection = ToolCollection(tool)

        result = await collection.execute(
            name="mock_tool", tool_input={"arg1": "value1"}
        )

        assert isinstance(result, ToolResult)
        assert result.output is not None
        assert "Executed with" in str(result.output)
        assert tool.was_called is True
        assert tool.call_args == {"arg1": "value1"}

    @pytest.mark.asyncio
    async def test_execute_invalid_tool(self):
        """Test execute returns failure for invalid tool name."""
        tool = MockTool()
        collection = ToolCollection(tool)

        result = await collection.execute(name="non_existent_tool")

        assert isinstance(result, ToolFailure)
        assert "non_existent_tool" in result.error
        assert "invalid" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_tool_raises_tool_error(self):
        """Test execute handles ToolError correctly."""
        tool = MockTool(should_fail=True, error_message="Custom error")
        collection = ToolCollection(tool)

        result = await collection.execute(name="mock_tool", tool_input={})

        assert isinstance(result, ToolFailure)
        assert "Custom error" in result.error

    @pytest.mark.asyncio
    async def test_execute_no_tool_input(self):
        """Test execute with no tool_input."""
        tool = MockTool()
        collection = ToolCollection(tool)

        result = await collection.execute(name="mock_tool", tool_input={})

        assert result.output is not None
        assert tool.was_called is True
        assert tool.call_args == {}

    @pytest.mark.asyncio
    async def test_execute_all_success(self):
        """Test execute_all runs all tools."""
        tool1 = MockTool()
        tool2 = AnotherMockTool()
        collection = ToolCollection(tool1, tool2)

        results = await collection.execute_all()

        assert len(results) == 2
        assert all(isinstance(r, ToolResult) for r in results)

    @pytest.mark.asyncio
    async def test_execute_all_with_failure(self):
        """Test execute_all handles tool failures."""
        tool1 = MockTool(should_fail=True, error_message="Error 1")
        tool2 = AnotherMockTool()
        collection = ToolCollection(tool1, tool2)

        results = await collection.execute_all()

        assert len(results) == 2
        assert isinstance(results[0], ToolFailure)
        assert "Error 1" in results[0].error
        assert results[1].output is not None

    @pytest.mark.asyncio
    async def test_execute_all_empty_collection(self):
        """Test execute_all on empty collection."""
        collection = ToolCollection()

        results = await collection.execute_all()

        assert len(results) == 0

    def test_get_tool_exists(self):
        """Test get_tool returns tool when it exists."""
        tool = MockTool()
        collection = ToolCollection(tool)

        result = collection.get_tool("mock_tool")

        assert result is tool

    def test_get_tool_not_exists(self):
        """Test get_tool returns None for non-existent tool."""
        collection = ToolCollection()

        result = collection.get_tool("non_existent")

        assert result is None

    def test_add_tool_new(self):
        """Test add_tool adds a new tool."""
        collection = ToolCollection()
        tool = MockTool()

        result = collection.add_tool(tool)

        assert len(collection.tools) == 1
        assert collection.tool_map["mock_tool"] is tool
        assert result is collection

    def test_add_tool_duplicate(self):
        """Test add_tool skips duplicate tool names."""
        tool1 = MockTool()
        tool2 = MockTool()  # Same name as tool1
        collection = ToolCollection(tool1)

        collection.add_tool(tool2)

        # Should still have only one tool (the original)
        assert len(collection.tools) == 1
        assert collection.tool_map["mock_tool"] is tool1

    def test_add_tools_multiple(self):
        """Test add_tools adds multiple tools."""
        tool1 = MockTool()
        tool2 = AnotherMockTool()
        collection = ToolCollection()

        collection.add_tools(tool1, tool2)

        assert len(collection.tools) == 2
        assert "mock_tool" in collection.tool_map
        assert "another_tool" in collection.tool_map

    def test_add_tools_with_duplicates(self):
        """Test add_tools skips duplicate tool names."""
        tool1 = MockTool()
        tool2 = AnotherMockTool()
        tool3 = MockTool()  # Duplicate of tool1
        collection = ToolCollection()

        collection.add_tools(tool1, tool2, tool3)

        assert len(collection.tools) == 2
        assert "mock_tool" in collection.tool_map
        assert "another_tool" in collection.tool_map
