"""Unit tests for PythonExecute tool."""

import pytest

from nura.tool.python_execute import PythonExecute


@pytest.mark.unit
class TestPythonExecute:
    """Test PythonExecute tool."""

    def test_python_execute_creation(self):
        """Test creating a PythonExecute tool."""
        tool = PythonExecute()
        assert tool.name == "python_execute"
        assert "python" in tool.description.lower()
        assert "code" in tool.parameters["properties"]

    def test_python_execute_parameters(self):
        """Test PythonExecute parameters schema."""
        tool = PythonExecute()
        params = tool.parameters

        assert params["type"] == "object"
        assert "code" in params["required"]
        assert "code" in params["properties"]

    @pytest.mark.asyncio
    async def test_execute_simple_print(self):
        """Test executing simple print code."""
        tool = PythonExecute()
        result = await tool.execute(code="print('hello world')")

        assert "observation" in result
        assert "hello world" in result["observation"]
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_arithmetic(self):
        """Test executing arithmetic operations."""
        tool = PythonExecute()
        result = await tool.execute(code="print(2 + 2)")

        assert "observation" in result
        assert "4" in result["observation"]
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_error(self):
        """Test executing code with error."""
        tool = PythonExecute()
        result = await tool.execute(code="print(undefined_variable)")

        assert "observation" in result
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_syntax_error(self):
        """Test executing code with syntax error."""
        tool = PythonExecute()
        result = await tool.execute(code="print('hello")

        assert "observation" in result
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test executing code with timeout."""
        tool = PythonExecute()
        # Use a very short timeout to trigger timeout handling
        result = await tool.execute(code="import time; time.sleep(10)", timeout=1)

        assert "observation" in result
        assert "timeout" in result["observation"].lower()
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_with_timeout_parameter(self):
        """Test executing with custom timeout parameter."""
        tool = PythonExecute()
        result = await tool.execute(code="print('test')", timeout=10)

        assert "observation" in result
        assert result["success"] is True

    def test_to_param(self):
        """Test tool to param conversion."""
        tool = PythonExecute()
        tool_dict = tool.to_param()

        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "python_execute"
        assert "parameters" in tool_dict["function"]
