"""Global pytest fixtures and configuration."""

import os
import pytest
from unittest.mock import MagicMock

# === Environment Isolation ===


@pytest.fixture(autouse=True)
def isolate_environment(tmp_path, monkeypatch):
    """Isolate test environment (auto-use for all tests)."""
    # Create isolated directories
    temp_home = tmp_path / "home"
    temp_config = tmp_path / "config"
    temp_data = tmp_path / "data"
    temp_cache = tmp_path / "cache"

    for dir in [temp_home, temp_config, temp_data, temp_cache]:
        dir.mkdir(parents=True, exist_ok=True)

    # Set environment variables
    monkeypatch.setenv("HOME", str(temp_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(temp_config))
    monkeypatch.setenv("XDG_DATA_HOME", str(temp_data))
    monkeypatch.setenv("XDG_CACHE_HOME", str(temp_cache))

    # Clear sensitive credentials
    for key in ["OPENAI_API_KEY", "FEISHU_APP_ID", "FEISHU_APP_SECRET"]:
        monkeypatch.delenv(key, raising=False)

    yield {
        "home": temp_home,
        "config": temp_config,
        "data": temp_data,
        "cache": temp_cache,
    }


# === LLM Fixtures ===


@pytest.fixture
def llm_config():
    """Load real LLM configuration from default.toml."""
    from nura.core.config import config

    # config.llm returns a dict like {'default': LLMSettings(...), ...}
    # Return the default LLMSettings object
    return config.llm.get("default")


@pytest.fixture
def real_llm(llm_config):
    """Create real LLM instance for integration tests.

    This fixture creates an LLM instance using the real configuration
    from default.toml. Use this for integration tests that need actual API calls.
    """
    from nura.llm import LLM

    # Clear instances to ensure fresh creation with test config
    LLM._instances.clear()

    # llm_config fixture now returns LLMSettings object directly
    llm = LLM(config_name="default", llm_config=llm_config)
    yield llm
    # Cleanup after test
    LLM._instances.clear()


@pytest.fixture
def mock_llm():
    """Create a mocked LLM instance for unit tests.

    This fixture provides a mock LLM that doesn't make real API calls.
    """
    from nura.llm import LLM
    from nura.llm.adapters import OpenAIMessageAdapter

    # Clear instances to ensure fresh creation
    LLM._instances.clear()

    # Create a mock LLM instance
    llm = LLM.__new__(LLM)
    llm.model = "gpt-4"
    llm.max_tokens = 4096
    llm.temperature = 0.7
    llm.api_type = "openai"
    llm.api_key = "test-key"
    llm.api_version = "v1"
    llm.base_url = "https://api.openai.com/v1"
    llm.total_input_tokens = 0
    llm.total_completion_tokens = 0
    llm.max_input_tokens = None
    llm.token_counter = MagicMock()
    llm.token_counter.count_message_tokens = MagicMock(return_value=100)
    # Set adapter for provider detection
    llm._adapter = OpenAIMessageAdapter()

    return llm


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "live: Live tests with real credentials")


def pytest_collection_modifyitems(config, items):
    """Skip live tests unless explicitly enabled."""
    if not (os.getenv("NURA_LIVE_TEST") == "1" or os.getenv("LIVE") == "1"):
        skip_live = pytest.mark.skip(reason="Live tests require NURA_LIVE_TEST=1")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)
