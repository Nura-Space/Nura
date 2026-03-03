"""Configuration file loaders and utilities.

Supports loading configuration from TOML, JSON, and YAML files with deep merge.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import tomllib
except ImportError:
    import tomli as tomllib

import yaml
from loguru import logger


def load_toml(path: Union[str, Path]) -> Dict[str, Any]:
    """Load configuration from TOML file.

    Args:
        path: Path to the TOML file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file cannot be parsed
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"TOML file not found: {path}")

    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse TOML file {path}: {e}")


def load_json(path: Union[str, Path]) -> Dict[str, Any]:
    """Load configuration from JSON file.

    Args:
        path: Path to the JSON file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file cannot be parsed
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse JSON file {path}: {e}")


def load_yaml(path: Union[str, Path]) -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        path: Path to the YAML file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file cannot be parsed
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        raise ValueError(f"Failed to parse YAML file {path}: {e}")


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence.

    Args:
        base: Base dictionary
        override: Override dictionary (higher priority)

    Returns:
        Merged dictionary (new dict, original dicts unchanged)

    Example:
        >>> base = {"a": 1, "b": {"c": 2, "d": 3}}
        >>> override = {"b": {"d": 4, "e": 5}, "f": 6}
        >>> deep_merge(base, override)
        {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = deep_merge(result[key], value)
        else:
            # Override value
            result[key] = value

    return result


def load_config_file(path: Union[str, Path]) -> Dict[str, Any]:
    """Load configuration file based on extension.

    Supports .toml, .json, .yaml, .yml files.

    Args:
        path: Path to the configuration file

    Returns:
        Configuration dictionary

    Raises:
        ValueError: If file extension is not supported
        FileNotFoundError: If the file doesn't exist
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".toml":
        return load_toml(path)
    elif suffix == ".json":
        return load_json(path)
    elif suffix in (".yaml", ".yml"):
        return load_yaml(path)
    else:
        raise ValueError(f"Unsupported config file extension: {suffix}")


def find_config_file(
    name: str, search_dirs: Optional[list[Path]] = None
) -> Optional[Path]:
    """Find configuration file by name in search directories.

    Searches for files with extensions: .toml, .json, .yaml, .yml

    Args:
        name: Base name of config file (without extension)
        search_dirs: Directories to search (defaults to [PROJECT_ROOT/config])

    Returns:
        Path to the first matching file, or None if not found
    """
    from nura.config.env import get_project_root

    if search_dirs is None:
        search_dirs = [get_project_root() / "config"]

    extensions = [".toml", ".json", ".yaml", ".yml"]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for ext in extensions:
            config_path = search_dir / f"{name}{ext}"
            if config_path.exists():
                logger.debug(f"Found config file: {config_path}")
                return config_path

    return None


def load_mcp_servers(config_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load MCP server configuration from mcp.json.

    Args:
        config_dir: Directory containing mcp.json (defaults to PROJECT_ROOT/config)

    Returns:
        Dictionary of MCP server configurations
    """
    from nura.config.env import get_project_root

    if config_dir is None:
        config_dir = get_project_root() / "config"

    config_path = config_dir / "mcp.json"

    if not config_path.exists():
        logger.debug(f"MCP config file not found: {config_path}")
        return {}

    try:
        data = load_json(config_path)
        servers = {}

        for server_id, server_config in data.get("mcpServers", {}).items():
            servers[server_id] = {
                "type": server_config["type"],
                "url": server_config.get("url"),
                "command": server_config.get("command"),
                "args": server_config.get("args", []),
            }

        logger.debug(f"Loaded {len(servers)} MCP servers from {config_path}")
        return servers
    except Exception as e:
        logger.warning(f"Failed to load MCP server config: {e}")
        return {}
