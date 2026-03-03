"""
DEPRECATED: This module is deprecated. Use nura.config instead.

This module is kept for backward compatibility but will be removed in a future version.
Please migrate to the new configuration system:

    Old:
        from nura.core.config import config
        api_key = config.llm["default"].api_key

    New:
        from nura.config import get_config
        config = get_config()
        api_key = config.llm["default"].api_key
"""

import json
import threading
import warnings

try:
    import tomllib
except ImportError:
    import tomli as tomllib
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field

from nura.config.models import (
    BrowserSettings,
    DaytonaSettings,
    LLMSettings,
    MCPServerConfig,
    MCPSettings,
    MemorySettings,
    ProxySettings,
    RunflowSettings,
    SandboxSettings,
    SearchSettings,
)


def get_project_root() -> Path:
    """Get the project root directory"""
    # From nura/core/config.py -> go up to project root (../../..)
    return Path(__file__).resolve().parent.parent.parent


PROJECT_ROOT = get_project_root()
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"


def load_mcp_server_config() -> Dict[str, MCPServerConfig]:
    """Load MCP server configuration from JSON file."""
    config_path = PROJECT_ROOT / "config" / "mcp.json"

    try:
        config_file = config_path if config_path.exists() else None
        if not config_file:
            return {}

        with config_file.open() as f:
            data = json.load(f)
            servers = {}

            for server_id, server_config in data.get("mcpServers", {}).items():
                servers[server_id] = MCPServerConfig(
                    type=server_config["type"],
                    url=server_config.get("url"),
                    command=server_config.get("command"),
                    args=server_config.get("args", []),
                )
            return servers
    except Exception as e:
        raise ValueError(f"Failed to load MCP server config: {e}")


class AppConfig(BaseModel):
    llm: Dict[str, LLMSettings]
    sandbox: Optional[SandboxSettings] = Field(
        None, description="Sandbox configuration"
    )
    browser_config: Optional[BrowserSettings] = Field(
        None, description="Browser configuration"
    )
    search_config: Optional[SearchSettings] = Field(
        None, description="Search configuration"
    )
    mcp_config: Optional[MCPSettings] = Field(None, description="MCP configuration")
    run_flow_config: Optional[RunflowSettings] = Field(
        None, description="Run flow configuration"
    )
    daytona_config: Optional[DaytonaSettings] = Field(
        None, description="Daytona configuration"
    )
    memory_config: Optional[MemorySettings] = Field(
        None, description="Memory configuration"
    )

    class Config:
        arbitrary_types_allowed = True


class Config:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    self._load_initial_config()
                    self._initialized = True

    @staticmethod
    def _get_config_path() -> Path:
        root = PROJECT_ROOT
        config_path = root / "config" / "default.toml"
        if config_path.exists():
            return config_path
        example_path = root / "config" / "default.example.toml"
        if example_path.exists():
            return example_path
        raise FileNotFoundError("No configuration file found in config directory")

    def _load_config(self) -> dict:
        config_path = self._get_config_path()
        with config_path.open("rb") as f:
            return tomllib.load(f)

    def _load_initial_config(self):
        raw_config = self._load_config()
        base_llm = raw_config.get("llm", {})
        llm_overrides = {
            k: v for k, v in raw_config.get("llm", {}).items() if isinstance(v, dict)
        }

        default_settings = {
            "model": base_llm.get("model"),
            "base_url": base_llm.get("base_url"),
            "api_key": base_llm.get("api_key"),
            "max_tokens": base_llm.get("max_tokens", 4096),
            "max_input_tokens": base_llm.get("max_input_tokens"),
            "temperature": base_llm.get("temperature", 1.0),
            "api_type": base_llm.get("api_type", ""),
            "api_version": base_llm.get("api_version", ""),
            "cache_ttl": base_llm.get("cache_ttl", 3600),
        }

        # handle browser config.
        browser_config = raw_config.get("browser", {})
        browser_settings = None

        if browser_config:
            # handle proxy settings.
            proxy_config = browser_config.get("proxy", {})
            proxy_settings = None

            if proxy_config and proxy_config.get("server"):
                proxy_settings = ProxySettings(
                    **{
                        k: v
                        for k, v in proxy_config.items()
                        if k in ["server", "username", "password"] and v
                    }
                )

            # filter valid browser config parameters.
            valid_browser_params = {
                k: v
                for k, v in browser_config.items()
                if k in BrowserSettings.__annotations__ and v is not None
            }

            # if there is proxy settings, add it to the parameters.
            if proxy_settings:
                valid_browser_params["proxy"] = proxy_settings

            # only create BrowserSettings when there are valid parameters.
            if valid_browser_params:
                browser_settings = BrowserSettings(**valid_browser_params)

        search_config = raw_config.get("search", {})
        search_settings = None
        if search_config:
            search_settings = SearchSettings(**search_config)
        sandbox_config = raw_config.get("sandbox", {})
        if sandbox_config:
            sandbox_settings = SandboxSettings(**sandbox_config)
        else:
            sandbox_settings = SandboxSettings()
        daytona_config = raw_config.get("daytona", {})
        if daytona_config:
            daytona_settings = DaytonaSettings(**daytona_config)
        else:
            daytona_settings = DaytonaSettings()

        mcp_config = raw_config.get("mcp", {})
        mcp_settings = None
        if mcp_config:
            # Load server configurations from JSON
            mcp_config["servers"] = load_mcp_server_config()
            mcp_settings = MCPSettings(**mcp_config)
        else:
            mcp_settings = MCPSettings(servers=load_mcp_server_config())

        run_flow_config = raw_config.get("runflow")
        if run_flow_config:
            run_flow_settings = RunflowSettings(**run_flow_config)
        else:
            run_flow_settings = RunflowSettings()

        memory_config = raw_config.get("memory", {})
        if memory_config:
            memory_settings = MemorySettings(**memory_config)
        else:
            memory_settings = MemorySettings()

        config_dict = {
            "llm": {
                "default": default_settings,
                **{
                    name: {**default_settings, **override_config}
                    for name, override_config in llm_overrides.items()
                },
            },
            "sandbox": sandbox_settings,
            "browser_config": browser_settings,
            "search_config": search_settings,
            "mcp_config": mcp_settings,
            "run_flow_config": run_flow_settings,
            "daytona_config": daytona_settings,
            "memory_config": memory_settings,
        }

        self._config = AppConfig(**config_dict)

    @property
    def llm(self) -> Dict[str, LLMSettings]:
        return self._config.llm

    @property
    def sandbox(self) -> SandboxSettings:
        return self._config.sandbox

    @property
    def daytona(self) -> DaytonaSettings:
        return self._config.daytona_config

    @property
    def browser_config(self) -> Optional[BrowserSettings]:
        return self._config.browser_config

    @property
    def search_config(self) -> Optional[SearchSettings]:
        return self._config.search_config

    @property
    def mcp_config(self) -> MCPSettings:
        """Get the MCP configuration"""
        return self._config.mcp_config

    @property
    def run_flow_config(self) -> RunflowSettings:
        """Get the Run Flow configuration"""
        return self._config.run_flow_config

    @property
    def memory_config(self) -> Optional[MemorySettings]:
        """Get the Memory configuration"""
        return self._config.memory_config

    @property
    def workspace_root(self) -> Path:
        """Get the workspace root directory"""
        return WORKSPACE_ROOT

    @property
    def root_path(self) -> Path:
        """Get the root path of the application"""
        return PROJECT_ROOT


# Issue deprecation warning
warnings.warn(
    "nura.core.config is deprecated and will be removed in a future version. "
    "Please use 'from nura.config import get_config' instead. "
    "See documentation for migration guide.",
    DeprecationWarning,
    stacklevel=2,
)

config = Config()
