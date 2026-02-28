"""Unit tests for CreateChatCompletion tool."""
import pytest
from pydantic import BaseModel
from typing import List, Dict, Optional, Union

from nura.tool.create_chat_completion import CreateChatCompletion


# Test models
class UserInfo(BaseModel):
    name: str
    age: int


class Address(BaseModel):
    city: str
    country: str


@pytest.mark.unit
class TestCreateChatCompletion:
    """Test CreateChatCompletion tool."""

    def test_creation_with_string_type(self):
        """Test creating tool with string type."""
        tool = CreateChatCompletion(response_type=str)

        assert tool.name == "create_chat_completion"
        assert tool.response_type == str
        assert "response" in tool.parameters["properties"]

    def test_creation_with_pydantic_model(self):
        """Test creating tool with Pydantic model."""
        tool = CreateChatCompletion(response_type=UserInfo)

        assert tool.response_type == UserInfo
        assert "name" in tool.parameters["properties"]
        assert "age" in tool.parameters["properties"]

    def test_creation_with_list_type(self):
        """Test creating tool with List type."""
        tool = CreateChatCompletion(response_type=List[str])

        assert "response" in tool.parameters["properties"]
        assert tool.parameters["properties"]["response"]["type"] == "array"

    def test_creation_with_dict_type(self):
        """Test creating tool with Dict type."""
        tool = CreateChatCompletion(response_type=Dict[str, int])

        assert "response" in tool.parameters["properties"]
        assert tool.parameters["properties"]["response"]["type"] == "object"

    def test_creation_with_union_type(self):
        """Test creating tool with Union type."""
        tool = CreateChatCompletion(response_type=Union[str, int])

        assert "response" in tool.parameters["properties"]

    def test_creation_with_custom_required(self):
        """Test with custom required fields."""
        tool = CreateChatCompletion(response_type=UserInfo)
        tool.required = ["name"]

        assert "name" in tool.required
        assert "age" not in tool.required

    def test_creation_with_default_required(self):
        """Test with default required fields."""
        tool = CreateChatCompletion(response_type=str)

        assert tool.required == ["response"]

    def test_parameters_with_pydantic_model(self):
        """Test parameters schema with Pydantic model."""
        tool = CreateChatCompletion(response_type=UserInfo)
        params = tool.parameters

        assert params["type"] == "object"
        assert "properties" in params

    def test_parameters_with_optional_required(self):
        """Test parameters with empty required list."""
        tool = CreateChatCompletion(response_type=str)

        params = tool.parameters

        # Even with empty required, _build_parameters uses default
        assert "required" in params

    @pytest.mark.asyncio
    async def test_execute_string_response(self):
        """Test execute with string response."""
        tool = CreateChatCompletion(response_type=str)

        result = await tool.execute(response="Hello world")

        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_execute_pydantic_response(self):
        """Test execute with Pydantic model response."""
        tool = CreateChatCompletion(response_type=UserInfo)

        result = await tool.execute(name="John", age=30)

        assert isinstance(result, UserInfo)
        assert result.name == "John"
        assert result.age == 30

    @pytest.mark.asyncio
    async def test_execute_list_response(self):
        """Test execute with List response."""
        tool = CreateChatCompletion(response_type=List[str])

        result = await tool.execute(response=["a", "b", "c"])

        assert result == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_execute_dict_response(self):
        """Test execute with Dict response."""
        tool = CreateChatCompletion(response_type=Dict[str, int])

        result = await tool.execute(response={"a": 1, "b": 2})

        assert result == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_execute_multiple_required_fields(self):
        """Test execute with multiple required fields."""
        tool = CreateChatCompletion(response_type=UserInfo)

        result = await tool.execute(name="John", age=30)

        # When passing all required fields for Pydantic model, returns the model
        assert isinstance(result, UserInfo)
        assert result.name == "John"
        assert result.age == 30

    @pytest.mark.asyncio
    async def test_execute_missing_field(self):
        """Test execute with missing required field."""
        tool = CreateChatCompletion(response_type=UserInfo)

        # Missing age field - Pydantic will raise ValidationError
        with pytest.raises(Exception):
            await tool.execute(name="John")

    @pytest.mark.asyncio
    async def test_execute_type_conversion_error(self):
        """Test execute with type conversion error."""
        tool = CreateChatCompletion(response_type=int)

        # This will try to convert "not a number" to int and fail
        result = await tool.execute(response="not a number")

        # Should fall back to returning the original value
        assert result == "not a number"

    @pytest.mark.asyncio
    async def test_execute_int_response(self):
        """Test execute with int response."""
        tool = CreateChatCompletion(response_type=int)

        result = await tool.execute(response=42)

        assert result == 42

    @pytest.mark.asyncio
    async def test_execute_float_response(self):
        """Test execute with float response."""
        tool = CreateChatCompletion(response_type=float)

        result = await tool.execute(response=3.14)

        assert result == 3.14

    @pytest.mark.asyncio
    async def test_execute_bool_response(self):
        """Test execute with bool response."""
        tool = CreateChatCompletion(response_type=bool)

        result = await tool.execute(response=True)

        assert result is True

    @pytest.mark.asyncio
    async def test_execute_custom_required_fields(self):
        """Test execute with custom required fields."""
        tool = CreateChatCompletion(response_type=UserInfo)

        result = await tool.execute(name="Alice", age=25, extra="ignored")

        # When multiple required fields passed as kwargs to Pydantic model,
        # returns the Pydantic model instance
        assert isinstance(result, UserInfo)
        assert result.name == "Alice"
        assert result.age == 25

    @pytest.mark.asyncio
    async def test_execute_no_required(self):
        """Test execute with no required fields."""
        tool = CreateChatCompletion(response_type=str)
        tool.required = []

        result = await tool.execute(some_field="value")

        # With no required fields, falls back to "response" field
        assert result == ""

    @pytest.mark.asyncio
    async def test_execute_list_with_pydantic_items(self):
        """Test execute with List of Pydantic models."""
        tool = CreateChatCompletion(response_type=List[Address])

        result = await tool.execute(response=[{"city": "Beijing", "country": "China"}])

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_execute_empty_response(self):
        """Test execute with empty response."""
        tool = CreateChatCompletion(response_type=str)

        result = await tool.execute()

        # Default required field "response" is used
        assert result == ""

    def test_to_param(self):
        """Test tool to param conversion."""
        tool = CreateChatCompletion(response_type=str)
        tool_dict = tool.to_param()

        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "create_chat_completion"
        assert "parameters" in tool_dict["function"]


@pytest.mark.unit
class TestCreateChatCompletionSchema:
    """Test CreateChatCompletion schema generation."""

    def test_schema_with_nested_model(self):
        """Test schema with nested Pydantic model."""
        class NestedModel(BaseModel):
            value: str

        class OuterModel(BaseModel):
            nested: NestedModel

        tool = CreateChatCompletion(response_type=OuterModel)

        # Should have nested properties
        assert "properties" in tool.parameters

    def test_schema_with_optional_fields(self):
        """Test schema with optional fields."""
        class OptionalModel(BaseModel):
            required_field: str
            optional_field: Optional[str] = None

        tool = CreateChatCompletion(response_type=OptionalModel)

        assert "properties" in tool.parameters
        assert "required_field" in tool.parameters["properties"]


@pytest.mark.unit
class TestCreateChatCompletionEdgeCases:
    """Test CreateChatCompletion edge cases."""

    @pytest.mark.asyncio
    async def test_execute_with_extra_kwargs(self):
        """Test execute with extra keyword arguments."""
        tool = CreateChatCompletion(response_type=str)

        result = await tool.execute(
            response="test",
            extra_field="extra",
            another_field=123
        )

        assert result == "test"

    @pytest.mark.asyncio
    async def test_execute_list_int(self):
        """Test execute with List[int]."""
        tool = CreateChatCompletion(response_type=List[int])

        result = await tool.execute(response=[1, 2, 3])

        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_execute_dict_mixed(self):
        """Test execute with Dict[str, Any]."""
        from typing import Any

        tool = CreateChatCompletion(response_type=Dict[str, Any])

        result = await tool.execute(response={"key": "value", "num": 42})

        assert result == {"key": "value", "num": 42}
