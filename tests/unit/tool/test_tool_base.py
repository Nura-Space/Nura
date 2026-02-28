"""Tests for nura/tool/base.py"""
import pytest
from unittest.mock import patch
import json
from typing import Any, Optional

from nura.tool.base import ToolResult, BaseTool, CLIResult, ToolFailure


class TestToolResult:
    """Unit tests for ToolResult."""

    def test_creation_default(self):
        """Test ToolResult default creation."""
        result = ToolResult()
        assert result.output is None
        assert result.error is None
        assert result.base64_image is None
        assert result.system is None

    def test_creation_with_output(self):
        """Test ToolResult creation with output."""
        result = ToolResult(output="test output")
        assert result.output == "test output"

    def test_creation_with_error(self):
        """Test ToolResult creation with error."""
        result = ToolResult(error="test error")
        assert result.error == "test error"

    def test_bool_with_output(self):
        """Test __bool__ returns True when output exists."""
        result = ToolResult(output="test")
        assert bool(result) is True

    def test_bool_with_error(self):
        """Test __bool__ returns True when error exists."""
        result = ToolResult(error="test error")
        assert bool(result) is True

    def test_bool_with_base64_image(self):
        """Test __bool__ returns True when base64_image exists."""
        result = ToolResult(base64_image="abc123")
        assert bool(result) is True

    def test_bool_with_system(self):
        """Test __bool__ returns True when system exists."""
        result = ToolResult(system="system info")
        assert bool(result) is True

    def test_bool_empty(self):
        """Test __bool__ returns False when all fields are None."""
        result = ToolResult()
        assert bool(result) is False

    def test_add_two_results_with_output(self):
        """Test __add__ combines two results with output."""
        result1 = ToolResult(output="first")
        result2 = ToolResult(output="second")
        combined = result1 + result2

        assert combined.output == "firstsecond"

    def test_add_two_results_with_error(self):
        """Test __add__ combines two results with error."""
        result1 = ToolResult(error="error1")
        result2 = ToolResult(error="error2")
        combined = result1 + result2

        assert combined.error == "error1error2"

    def test_add_mixed_results(self):
        """Test __add__ with one output and one error."""
        result1 = ToolResult(output="output")
        result2 = ToolResult(error="error")
        combined = result1 + result2

        assert combined.output == "output"
        assert combined.error == "error"

    def test_add_with_base64_raises(self):
        """Test __add__ raises ValueError when both have base64_image."""
        result1 = ToolResult(base64_image="img1")
        result2 = ToolResult(base64_image="img2")

        with pytest.raises(ValueError):
            _ = result1 + result2

    def test_str_with_output(self):
        """Test __str__ returns output when no error."""
        result = ToolResult(output="test output")
        assert str(result) == "test output"

    def test_str_with_error(self):
        """Test __str__ returns error when error exists."""
        result = ToolResult(error="test error")
        assert str(result) == "Error: test error"

    def test_replace_with_output(self):
        """Test replace method replaces output."""
        result = ToolResult(output="old")
        new_result = result.replace(output="new")

        assert new_result.output == "new"
        assert new_result.error is None

    def test_replace_with_error(self):
        """Test replace method replaces error."""
        result = ToolResult(error="old error")
        new_result = result.replace(error="new error")

        assert new_result.error == "new error"

    def test_replace_preserves_other_fields(self):
        """Test replace method preserves other fields."""
        result = ToolResult(output="output", error="error", system="system")
        new_result = result.replace(output="new output")

        assert new_result.output == "new output"
        assert new_result.error == "error"
        assert new_result.system == "system"


class TestToolFailure:
    """Unit tests for ToolFailure."""

    def test_creation(self):
        """Test ToolFailure creation."""
        failure = ToolFailure(error="failure message")
        assert failure.error == "failure message"

    def test_bool_true(self):
        """Test ToolFailure __bool__ returns True."""
        failure = ToolFailure(error="error")
        assert bool(failure) is True


class MockTool(BaseTool):
    """Mock tool for testing."""

    name: str = "mock_tool"
    description: str = "A mock tool"
    parameters: Optional[dict] = None

    model_config = {"arbitrary_types_allowed": True}

    async def execute(self, **kwargs) -> ToolResult:
        return self.success_response("executed")


class TestBaseTool:
    """Unit tests for BaseTool."""

    def test_initialization(self):
        """Test BaseTool initialization."""
        tool = MockTool()
        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool"

    def test_to_param(self):
        """Test to_param returns correct format."""
        tool = MockTool()
        param = tool.to_param()

        assert param["type"] == "function"
        assert param["function"]["name"] == "mock_tool"
        assert param["function"]["description"] == "A mock tool"
        assert param["function"]["parameters"] is None

    def test_success_response_string(self):
        """Test success_response with string."""
        tool = MockTool()
        result = tool.success_response("test message")

        assert isinstance(result, ToolResult)
        assert result.output == "test message"
        assert result.error is None

    def test_success_response_dict(self):
        """Test success_response with dict."""
        tool = MockTool()
        result = tool.success_response({"key": "value"})

        assert isinstance(result, ToolResult)
        assert "key" in result.output
        assert "value" in result.output

    def test_fail_response(self):
        """Test fail_response."""
        tool = MockTool()
        result = tool.fail_response("error message")

        assert isinstance(result, ToolResult)
        assert result.error == "error message"
        assert result.output is None

    @pytest.mark.asyncio
    async def test_call_execute(self):
        """Test __call__ calls execute."""
        tool = MockTool()
        result = await tool(arg1="value1")

        assert isinstance(result, ToolResult)
        assert result.output == "executed"
