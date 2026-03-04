"""Integration tests for LLM client with real API."""
import os
import pytest

from nura.llm.client import LLM
from nura.core.config import config


def check_api_key():
    """Check if API key is available."""
    # Check environment variable first
    if os.environ.get("OPENAI_API_KEY"):
        return True
    # Check config
    try:
        if config.llm and config.llm.api_key:
            return True
    except Exception:
        pass
    return False


HAS_API_KEY = check_api_key()


@pytest.fixture
def llm_client():
    """Create LLM client with real config."""
    if not HAS_API_KEY:
        pytest.skip("No API key available")
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
    """Test token limit check."""
    # Test with small text
    small_text = "Hello"
    assert llm_client.check_within_limit(small_text) is True

    # Test with large text
    large_text = "word " * 10000
    assert llm_client.check_within_limit(large_text) is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_streaming(llm_client):
    """Test streaming response."""
    messages = [{"role": "user", "content": "Count from 1 to 3."}]

    response = await llm_client.ask(
        messages=messages,
        stream=True,
        temperature=0.0
    )

    assert response is not None
    assert isinstance(response, str)
    print(f"Streaming response: {response}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_token_tracking(llm_client):
    """Test token tracking across multiple requests."""
    messages1 = [{"role": "user", "content": "Say 'First'."}]
    messages2 = [{"role": "user", "content": "Say 'Second'."}]

    await llm_client.ask(messages=messages1, stream=False)
    await llm_client.ask(messages=messages2, stream=False)

    # Check that tokens are being tracked
    total_tokens = llm_client.total_input_tokens + llm_client.total_output_tokens
    assert total_tokens > 0
    print(f"Total tokens tracked: {total_tokens}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_ask_with_different_temperatures(llm_client):
    """Test ask with different temperature values."""
    messages = [{"role": "user", "content": "Say 'Hello'."}]

    # Test with temperature 0 (deterministic)
    response1 = await llm_client.ask(messages=messages, temperature=0.0)
    response2 = await llm_client.ask(messages=messages, temperature=0.0)

    # With temperature 0, responses should be identical
    assert response1 == response2
    print(f"Response with temp 0: {response1}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_longer_conversation(llm_client):
    """Test longer conversation context."""
    messages = [
        {"role": "user", "content": "My name is TestUser."},
        {"role": "assistant", "content": "Hello TestUser! How can I help you?"},
        {"role": "user", "content": "What's my name?"}
    ]

    response = await llm_client.ask(
        messages=messages,
        stream=False,
        temperature=0.0
    )

    assert response is not None
    assert isinstance(response, str)
    # The response should mention the user's name
    assert "TestUser" in response
    print(f"Response: {response}")
