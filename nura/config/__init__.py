"""Nura configuration system.

This module provides a unified configuration management system with:
- Type-safe Pydantic models
- 4-layer configuration merging (defaults → files → env vars → runtime)
- Support for multiple platforms (Feishu, etc.)
- Environment variable overrides
- No singleton pattern (supports dependency injection)

Usage:
    Basic usage:
        >>> from nura.config import get_config
        >>> config = get_config()
        >>> api_key = config.llm["default"].api_key

    Platform-specific:
        >>> config = get_config(platform="feishu")
        >>> app_id = config.platforms.feishu.app_id

    With overrides:
        >>> config = get_config(overrides={"llm": {"default": {"model": "gpt-4"}}})

    For testing (dependency injection):
        >>> from nura.config import ConfigManager
        >>> manager = ConfigManager()
        >>> test_config = manager.load(overrides={"context": {"max_tokens": 1000}})
"""

from typing import Any, Dict, Optional

from nura.config.manager import ConfigManager
from nura.config.models import (
    BrowserSettings,
    ContextConfig,
    CoreSettings,
    DaytonaSettings,
    FeishuPlatformConfig,
    LLMSettings,
    MCPServerConfig,
    MCPSettings,
    MemorySettings,
    NuraConfig,
    PlatformConfig,
    ProxySettings,
    RunflowSettings,
    SandboxSettings,
    SearchSettings,
    TTSConfig,
)

__all__ = [
    # Main API
    "get_config",
    "ConfigManager",
    # Configuration models
    "NuraConfig",
    "LLMSettings",
    "ContextConfig",
    "MemorySettings",
    "CoreSettings",
    "BrowserSettings",
    "SandboxSettings",
    "SearchSettings",
    "MCPSettings",
    "MCPServerConfig",
    "RunflowSettings",
    "DaytonaSettings",
    "ProxySettings",
    "PlatformConfig",
    "FeishuPlatformConfig",
    "TTSConfig",
]

# Global configuration instance (not a singleton, just a cached instance)
_global_config: Optional[NuraConfig] = None


def get_config(
    platform: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
    reload: bool = False,
) -> NuraConfig:
    """Get global configuration instance.

    This is a factory function that creates or returns a cached configuration.
    It's not a singleton - you can always create new configurations using ConfigManager directly.

    Args:
        platform: Platform name for platform-specific config (e.g., "feishu")
        overrides: Runtime configuration overrides
        reload: Force reload configuration from files

    Returns:
        NuraConfig instance

    Example:
        >>> config = get_config()
        >>> config = get_config(platform="feishu")
        >>> config = get_config(overrides={"llm": {"default": {"model": "gpt-4"}}})
        >>> config = get_config(reload=True)  # Force reload
    """
    global _global_config

    if _global_config is None or reload:
        manager = ConfigManager()
        _global_config = manager.load(platform=platform, overrides=overrides)

    return _global_config
