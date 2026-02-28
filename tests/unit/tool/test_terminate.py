"""Unit tests for Terminate tool."""
import pytest

from nura.tool.terminate import Terminate


@pytest.mark.unit
class TestTerminate:
    """Test Terminate tool."""

    def test_terminate_creation(self):
        """Test creating a Terminate tool."""
        tool = Terminate()
        assert tool.name == "terminate"
        assert "terminate" in tool.description.lower()
        assert "status" in tool.parameters["properties"]

    def test_terminate_parameters(self):
        """Test Terminate parameters schema."""
        tool = Terminate()
        params = tool.parameters

        assert params["type"] == "object"
        assert "status" in params["required"]
        assert params["properties"]["status"]["type"] == "string"
        assert "success" in params["properties"]["status"]["enum"]
        assert "failure" in params["properties"]["status"]["enum"]

    @pytest.mark.asyncio
    async def test_execute_success_status(self):
        """Test execute with success status."""
        tool = Terminate()
        result = await tool.execute(status="success")

        assert "success" in result.lower()
        assert "completed" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_failure_status(self):
        """Test execute with failure status."""
        tool = Terminate()
        result = await tool.execute(status="failure")

        assert "failure" in result.lower()
        assert "completed" in result.lower()

    def test_to_param(self):
        """Test tool to param conversion."""
        tool = Terminate()
        tool_dict = tool.to_param()

        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "terminate"
        assert "parameters" in tool_dict["function"]
