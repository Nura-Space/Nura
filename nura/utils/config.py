"""Configuration utilities.

DEPRECATED: This module is deprecated. Use nura.config.loader instead.

Please migrate to the new configuration system:

    Old:
        from nura.utils.config import load_json_config
        config = load_json_config("config.json")

    New:
        from nura.config.loader import load_json
        config = load_json("config.json")
"""

import json
import warnings
from typing import Any, Dict

from loguru import logger

# Issue deprecation warning when module is imported
warnings.warn(
    "nura.utils.config is deprecated and will be removed in a future version. "
    "Please use 'from nura.config.loader import load_json' instead.",
    DeprecationWarning,
    stacklevel=2,
)


def load_json_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file.

    Args:
        config_path: Path to the JSON configuration file

    Returns:
        Configuration dictionary, or empty dict if loading fails
    """
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}
