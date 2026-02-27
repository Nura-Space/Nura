"""Integration tests for LLM client with real API."""
import pytest
import asyncio

from nura.llm.client import LLM
from nura.core.config import config


@pytest.fixture
def llm_client():
    """Create LLM client with real config."""
    # Clear singleton instances to get fresh client
    LLM._instances = {}
    return LLM("default")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_ask_basic(llm_client):
    """Test basic ask request with real API."""
    messages = [{"role": "user", "content": "Say 'Hello' in one word."}]

    response = await llm_client.ask(
        messages=messages,
        stream=False,
        temperature=0.0
    )

    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0
    print(f"Response: {response}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_ask_with_system_message(llm_client):
    """Test ask with system message."""
    system_msgs = [{"role": "system", "content": "You are a helpful assistant."}]
    messages = [{"role": "user", "content": "What is 1+1?"}]

    response = await llm_client.ask(
        messages=messages,
        system_msgs=system_msgs,
        stream=False,
        temperature=0.0
    )

    assert response is not None
    assert isinstance(response, str)
    print(f"Response: {response}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_count_tokens(llm_client):
    """Test token counting."""
    text = "This is a test message for token counting."
    count = llm_client.count_tokens(text)

    assert count > 0
    print(f"Token count for '{text}': {count}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_count_message_tokens(llm_client):
    """Test message token counting."""
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there!"}
    ]

    count = llm_client.count_message_tokens(messages)

    assert count > 0
    print(f"Message tokens: {count}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_check_token_limit(llm_client):
    """Test token limit checking."""
    # Set a specific limit for testing
    llm_client.max_input_tokens = 10000

    # Should pass with reasonable token count
    result = llm_client.check_token_limit(1000)
    assert result is True

    # Should fail with excessive token count
    result = llm_client.check_token_limit(20000)
    assert result is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_streaming(llm_client):
    """Test streaming response."""
    messages = [{"role": "user", "content": "Count from 1 to 5."}]

    response = await llm_client.ask(
        messages=messages,
        stream=True,
        temperature=0.0
    )

    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0
    print(f"Streaming response: {response}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_token_tracking(llm_client):
    """Test token usage tracking."""
    initial_input = llm_client.total_input_tokens
    initial_completion = llm_client.total_completion_tokens

    messages = [{"role": "user", "content": "Hello"}]
    await llm_client.ask(messages=messages, stream=False)

    # Token counts should have been updated
    print(f"Input tokens: {llm_client.total_input_tokens - initial_input}")
    print(f"Completion tokens: {llm_client.total_completion_tokens - initial_completion}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_ask_with_different_temperatures(llm_client):
    """Test ask with different temperature values."""
    messages = [{"role": "user", "content": "What is the capital of France?"}]

    # With temperature 0, should be deterministic
    response1 = await llm_client.ask(messages=messages, temperature=0.0, stream=False)

    # With temperature 1, may vary
    response2 = await llm_client.ask(messages=messages, temperature=1.0, stream=False)

    assert response1 is not None
    assert response2 is not None
    print(f"Response (temp=0): {response1}")
    print(f"Response (temp=1): {response2}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_longer_conversation(llm_client):
    """Test with longer conversation history."""
    messages = [
        {"role": "user", "content": "My name is Alice."},
        {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
        {"role": "user", "content": "What's my name?"},
    ]

    response = await llm_client.ask(
        messages=messages,
        stream=False,
        temperature=0.0
    )

    assert response is not None
    # Should remember the name
    print(f"Response: {response}")
