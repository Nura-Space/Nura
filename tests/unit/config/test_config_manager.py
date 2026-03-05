"""Tests for configuration manager."""

import pytest

from nura.config import get_config, ConfigManager
from nura.config.models import NuraConfig


@pytest.mark.unit
class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_create_manager(self):
        """Test creating ConfigManager instance."""
        manager = ConfigManager()
        assert manager is not None
        assert manager.project_root.exists()
        assert manager.config_dir.exists()

    def test_load_default_config(self):
        """Test loading default configuration."""
        manager = ConfigManager()
        config = manager.load()

        assert isinstance(config, NuraConfig)
        assert config.core.project_root is not None
        assert config.core.workspace_root is not None

    def test_load_with_overrides(self):
        """Test loading configuration with runtime overrides."""
        manager = ConfigManager()
        config = manager.load(
            overrides={
                "context": {"max_tokens": 100000, "keep_turns": 5},
                "memory": {"memory_dir": "/test/memory"},
            }
        )

        assert config.context.max_tokens == 100000
        assert config.context.keep_turns == 5
        assert config.memory.memory_dir == "/test/memory"

    def test_multiple_managers_independent(self):
        """Test that multiple ConfigManager instances are independent."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()

        config1 = manager1.load(overrides={"context": {"max_tokens": 100000}})
        config2 = manager2.load(overrides={"context": {"max_tokens": 50000}})

        assert config1.context.max_tokens == 100000
        assert config2.context.max_tokens == 50000


@pytest.mark.unit
class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_default(self):
        """Test getting default configuration."""
        config = get_config(reload=True)  # Force reload to avoid cache

        assert isinstance(config, NuraConfig)
        assert config.core.project_root is not None

    def test_get_config_with_overrides(self):
        """Test getting configuration with overrides."""
        config = get_config(overrides={"context": {"max_tokens": 200000}}, reload=True)

        assert config.context.max_tokens == 200000

    def test_get_config_caching(self):
        """Test that get_config caches the result."""
        config1 = get_config(reload=True)
        config2 = get_config()  # Should return same instance

        # Both should be NuraConfig instances
        assert isinstance(config1, NuraConfig)
        assert isinstance(config2, NuraConfig)
