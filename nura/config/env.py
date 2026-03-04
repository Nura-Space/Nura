"""Environment variable processing and utilities.

Handles loading environment variables from .env files and mapping them to configuration.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from nura.core.logger import logger


def get_project_root() -> Path:
    """Get the project root directory.

    Returns:
        Path to the project root (where nura package is located)
    """
    # From nura/config/env.py -> go up to project root (../../..)
    return Path(__file__).resolve().parent.parent.parent


def load_dotenv(env_path: Optional[Path] = None) -> None:
    """Load environment variables from .env file.

    Args:
        env_path: Path to .env file (defaults to PROJECT_ROOT/.env)
    """
    try:
        from dotenv import load_dotenv as _load_dotenv
    except ImportError:
        logger.debug("python-dotenv not installed, skipping .env file loading")
        return

    if env_path is None:
        env_path = get_project_root() / ".env"

    if env_path.exists():
        logger.debug(f"Loading environment variables from {env_path}")
        _load_dotenv(env_path, override=True)
    else:
        logger.debug(f".env file not found at {env_path}")


def parse_env_value(value: str) -> Any:
    """Parse environment variable value to appropriate Python type.

    Args:
        value: String value from environment variable

    Returns:
        Parsed value (bool, int, float, or str)

    Examples:
        >>> parse_env_value("true")
        True
        >>> parse_env_value("123")
        123
        >>> parse_env_value("1.5")
        1.5
        >>> parse_env_value("hello")
        "hello"
    """
    # Boolean
    if value.lower() in ("true", "yes", "1", "on"):
        return True
    if value.lower() in ("false", "no", "0", "off"):
        return False

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    # String (default)
    return value


def load_env_overrides() -> Dict[str, Any]:
    """Load configuration overrides from environment variables.

    Supports the following environment variable patterns:
    - NURA_<SECTION>_<KEY> - Core configuration (e.g., NURA_LLM_API_KEY)
    - <PLATFORM>_<KEY> - Platform-specific (e.g., FEISHU_APP_ID)

    Returns:
        Dictionary of configuration overrides

    Example:
        Environment variables:
            NURA_LLM_MODEL=gpt-4
            NURA_CONTEXT_MAX_TOKENS=100000
            FEISHU_APP_ID=cli_xxx

        Returns:
            {
                "llm": {"default": {"model": "gpt-4"}},
                "context": {"max_tokens": 100000},
                "platforms": {"feishu": {"app_id": "cli_xxx"}}
            }
    """
    overrides: Dict[str, Any] = {}

    # Process NURA_* environment variables
    for key, value in os.environ.items():
        if key.startswith("NURA_"):
            _process_nura_env(key, value, overrides)
        elif key.startswith("FEISHU_"):
            _process_platform_env("feishu", key, value, overrides)
        elif key.startswith("VOLCENGINE_"):
            _process_volcengine_env(key, value, overrides)

    return overrides


def _process_nura_env(key: str, value: str, overrides: Dict[str, Any]) -> None:
    """Process NURA_* environment variables.

    Args:
        key: Environment variable key (e.g., NURA_LLM_MODEL)
        value: Environment variable value
        overrides: Dictionary to update with parsed values
    """
    # Remove NURA_ prefix
    parts = key[5:].lower().split("_")

    if len(parts) < 2:
        logger.warning(f"Invalid NURA_* environment variable: {key}")
        return

    section = parts[0]  # e.g., "llm", "context", "memory"
    field = "_".join(parts[1:])  # e.g., "api_key", "max_tokens"

    # Special field mappings to match model field names
    # NURA_MEMORY_DIR -> memory.memory_dir (not memory.dir)
    field_mappings = {
        "memory": {
            "dir": "memory_dir",
        }
    }

    if section in field_mappings and field in field_mappings[section]:
        field = field_mappings[section][field]

    parsed_value = parse_env_value(value)

    # Special handling for LLM settings (apply to default profile)
    if section == "llm":
        if section not in overrides:
            overrides[section] = {}
        if "default" not in overrides[section]:
            overrides[section]["default"] = {}
        overrides[section]["default"][field] = parsed_value
    else:
        # Other sections
        if section not in overrides:
            overrides[section] = {}
        overrides[section][field] = parsed_value


def _process_platform_env(
    platform: str, key: str, value: str, overrides: Dict[str, Any]
) -> None:
    """Process platform-specific environment variables.

    Args:
        platform: Platform name (e.g., "feishu")
        key: Environment variable key (e.g., FEISHU_APP_ID)
        value: Environment variable value
        overrides: Dictionary to update with parsed values
    """
    # Remove platform prefix
    prefix_len = len(platform) + 1
    field = key[prefix_len:].lower()

    parsed_value = parse_env_value(value)

    if "platforms" not in overrides:
        overrides["platforms"] = {}
    if platform not in overrides["platforms"]:
        overrides["platforms"][platform] = {}

    overrides["platforms"][platform][field] = parsed_value


def _process_volcengine_env(key: str, value: str, overrides: Dict[str, Any]) -> None:
    """Process VOLCENGINE_* environment variables for TTS configuration.

    Args:
        key: Environment variable key (e.g., VOLCENGINE_TTS_TOKEN)
        value: Environment variable value
        overrides: Dictionary to update with parsed values
    """
    # Map VOLCENGINE_* to feishu.tts configuration
    if key == "VOLCENGINE_TTS_TOKEN":
        if "platforms" not in overrides:
            overrides["platforms"] = {}
        if "feishu" not in overrides["platforms"]:
            overrides["platforms"]["feishu"] = {}
        if "tts" not in overrides["platforms"]["feishu"]:
            overrides["platforms"]["feishu"]["tts"] = {}
        overrides["platforms"]["feishu"]["tts"]["access_token"] = value
    elif key == "VOLCENGINE_TTS_APP_ID":
        if "platforms" not in overrides:
            overrides["platforms"] = {}
        if "feishu" not in overrides["platforms"]:
            overrides["platforms"]["feishu"] = {}
        if "tts" not in overrides["platforms"]["feishu"]:
            overrides["platforms"]["feishu"]["tts"] = {}
        overrides["platforms"]["feishu"]["tts"]["app_id"] = value


# Environment variable documentation (for reference)
ENV_VAR_DOCS = """
Supported Environment Variables:

Core Configuration (NURA_* prefix):
  NURA_LLM_API_KEY         - LLM API key
  NURA_LLM_MODEL           - LLM model name
  NURA_LLM_BASE_URL        - LLM API base URL
  NURA_LLM_MAX_TOKENS      - Maximum tokens per request
  NURA_LLM_TEMPERATURE     - Sampling temperature
  NURA_CONTEXT_MAX_TOKENS  - Context window size
  NURA_CONTEXT_KEEP_TURNS  - Number of recent turns to keep
  NURA_MEMORY_DIR          - Memory storage directory

Platform Configuration:
  FEISHU_APP_ID            - Feishu app ID
  FEISHU_APP_SECRET        - Feishu app secret
  FEISHU_PROFILE_PATH      - Path to agent profile YAML
  VOLCENGINE_TTS_TOKEN     - Volcengine TTS access token
  VOLCENGINE_TTS_APP_ID    - Volcengine TTS app ID

Example .env file:
  # LLM Configuration
  NURA_LLM_API_KEY=sk-xxx
  NURA_LLM_MODEL=gpt-4
  NURA_LLM_BASE_URL=https://api.openai.com/v1

  # Feishu Platform
  FEISHU_APP_ID=cli_xxx
  FEISHU_APP_SECRET=secret_xxx

  # TTS
  VOLCENGINE_TTS_TOKEN=token_xxx
  VOLCENGINE_TTS_APP_ID=app_xxx
"""
