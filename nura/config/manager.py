"""Configuration manager for loading and merging configurations.

Implements the 4-layer configuration loading strategy:
1. Code defaults (Pydantic field defaults)
2. File configuration (TOML/JSON)
3. Environment variable overrides
4. Runtime overrides
"""

from pathlib import Path
from typing import Any, Dict, Optional

from nura.core.logger import logger

from nura.config.env import get_project_root, load_dotenv, load_env_overrides
from nura.config.loader import (
    deep_merge,
    find_config_file,
    load_config_file,
    load_mcp_servers,
)
from nura.config.models import (
    BrowserSettings,
    ContextConfig,
    CoreSettings,
    DaytonaSettings,
    FeishuPlatformConfig,
    LLMSettings,
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


class ConfigManager:
    """Configuration manager that loads and merges configurations from multiple sources.

    Usage:
        >>> manager = ConfigManager()
        >>> config = manager.load()  # Load default configuration
        >>> config = manager.load(platform="feishu")  # Load with platform-specific config
        >>> config = manager.load(overrides={"llm": {"default": {"model": "gpt-4"}}})
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_dir: Configuration directory (defaults to PROJECT_ROOT/config)
        """
        self.project_root = get_project_root()
        self.config_dir = config_dir or self.project_root / "config"
        self.workspace_root = self.project_root / "workspace"

    def load(
        self,
        platform: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> NuraConfig:
        """Load configuration with 4-layer merging strategy.

        Layer 1: Code defaults (Pydantic field defaults)
        Layer 2: File configuration (default.toml + platform-specific)
        Layer 3: Environment variable overrides
        Layer 4: Runtime overrides

        Args:
            platform: Platform name for platform-specific config (e.g., "feishu")
            overrides: Runtime configuration overrides

        Returns:
            Fully merged and validated NuraConfig object
        """
        # Layer 1: Code defaults (handled by Pydantic)
        config_dict: Dict[str, Any] = {}

        # Layer 2: Load file configurations
        file_config = self._load_file_config(platform)
        config_dict = deep_merge(config_dict, file_config)

        # Layer 3: Load environment variable overrides
        load_dotenv()  # Load .env file if present
        env_overrides = load_env_overrides()
        config_dict = deep_merge(config_dict, env_overrides)

        # Layer 4: Apply runtime overrides
        if overrides:
            config_dict = deep_merge(config_dict, overrides)

        # Add core settings
        if "core" not in config_dict:
            config_dict["core"] = {}
        config_dict["core"]["project_root"] = self.project_root
        config_dict["core"]["workspace_root"] = self.workspace_root

        # Parse and validate configuration
        return self._parse_config(config_dict)

    def _load_file_config(self, platform: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from files.

        Args:
            platform: Platform name for platform-specific config

        Returns:
            Merged configuration dictionary from files
        """
        config_dict: Dict[str, Any] = {}

        # Load default configuration
        default_config_path = find_config_file("default", [self.config_dir])
        if default_config_path:
            logger.info(f"Loading default config from {default_config_path}")
            try:
                default_config = load_config_file(default_config_path)
                config_dict = deep_merge(config_dict, default_config)
            except Exception as e:
                logger.warning(f"Failed to load default config: {e}")
        else:
            # Fallback to legacy config.toml
            legacy_config_path = self.config_dir / "config.toml"
            if legacy_config_path.exists():
                logger.info(f"Loading legacy config from {legacy_config_path}")
                try:
                    legacy_config = load_config_file(legacy_config_path)
                    config_dict = deep_merge(config_dict, legacy_config)
                except Exception as e:
                    logger.warning(f"Failed to load legacy config: {e}")

        # Load platform-specific configuration
        if platform:
            platform_config_path = find_config_file(
                platform, [self.config_dir / "platforms"]
            )
            if platform_config_path:
                logger.info(f"Loading platform config from {platform_config_path}")
                try:
                    platform_config = load_config_file(platform_config_path)
                    # Merge platform config into platforms.<platform> section
                    if "platforms" not in config_dict:
                        config_dict["platforms"] = {}
                    if platform not in config_dict["platforms"]:
                        config_dict["platforms"][platform] = {}
                    config_dict["platforms"][platform] = deep_merge(
                        config_dict["platforms"].get(platform, {}), platform_config
                    )
                except Exception as e:
                    logger.warning(f"Failed to load platform config: {e}")

        return config_dict

    def _parse_config(self, config_dict: Dict[str, Any]) -> NuraConfig:
        """Parse and validate configuration dictionary into NuraConfig.

        Args:
            config_dict: Raw configuration dictionary

        Returns:
            Validated NuraConfig object
        """
        # Parse LLM settings
        llm_config = self._parse_llm_config(config_dict.get("llm", {}))

        # Parse browser settings
        browser_config = self._parse_browser_config(config_dict.get("browser", {}))

        # Parse sandbox settings
        sandbox_config = config_dict.get("sandbox", {})
        sandbox_settings = SandboxSettings(**sandbox_config) if sandbox_config else None

        # Parse search settings
        search_config = config_dict.get("search", {})
        search_settings = SearchSettings(**search_config) if search_config else None

        # Parse MCP settings
        mcp_config = config_dict.get("mcp", {})
        if mcp_config or True:  # Always try to load MCP servers
            mcp_servers = load_mcp_servers(self.config_dir)
            if "servers" not in mcp_config:
                mcp_config["servers"] = mcp_servers
            mcp_settings = MCPSettings(**mcp_config) if mcp_config else None
        else:
            mcp_settings = None

        # Parse runflow settings
        runflow_config = config_dict.get("runflow", {})
        runflow_settings = RunflowSettings(**runflow_config) if runflow_config else None

        # Parse daytona settings
        daytona_config = config_dict.get("daytona", {})
        daytona_settings = DaytonaSettings(**daytona_config) if daytona_config else None

        # Parse memory settings
        memory_config = config_dict.get("memory", {})
        memory_settings = (
            MemorySettings(**memory_config) if memory_config else MemorySettings()
        )

        # Parse context settings
        context_config = config_dict.get("context", {})
        context_settings = (
            ContextConfig(**context_config) if context_config else ContextConfig()
        )

        # Parse core settings
        core_config = config_dict.get("core", {})
        core_settings = CoreSettings(**core_config)

        # Parse platform settings
        platforms_config = config_dict.get("platforms", {})
        platform_settings = self._parse_platform_config(platforms_config)

        # Create NuraConfig
        return NuraConfig(
            core=core_settings,
            llm=llm_config,
            context=context_settings,
            memory=memory_settings,
            browser=browser_config,
            sandbox=sandbox_settings,
            search=search_settings,
            mcp=mcp_settings,
            runflow=runflow_settings,
            daytona=daytona_settings,
            platforms=platform_settings,
        )

    def _parse_llm_config(self, llm_config: Dict[str, Any]) -> Dict[str, LLMSettings]:
        """Parse LLM configuration with profile support.

        Args:
            llm_config: Raw LLM configuration

        Returns:
            Dictionary of LLMSettings by profile name
        """
        if not llm_config:
            return {}

        # Extract base settings (for default profile)
        base_settings = {k: v for k, v in llm_config.items() if not isinstance(v, dict)}

        # Extract profile overrides
        profile_overrides = {k: v for k, v in llm_config.items() if isinstance(v, dict)}

        # Create default profile
        llm_settings = {}
        if base_settings:
            llm_settings["default"] = LLMSettings(**base_settings)

        # Create other profiles (merge with base settings)
        for profile_name, profile_config in profile_overrides.items():
            merged_config = {**base_settings, **profile_config}
            llm_settings[profile_name] = LLMSettings(**merged_config)

        return llm_settings

    def _parse_browser_config(
        self, browser_config: Dict[str, Any]
    ) -> Optional[BrowserSettings]:
        """Parse browser configuration.

        Args:
            browser_config: Raw browser configuration

        Returns:
            BrowserSettings object or None
        """
        if not browser_config:
            return None

        # Parse proxy settings
        proxy_config = browser_config.get("proxy", {})
        proxy_settings = None
        if proxy_config and proxy_config.get("server"):
            proxy_settings = ProxySettings(**proxy_config)

        # Filter valid browser parameters
        valid_params = {
            k: v
            for k, v in browser_config.items()
            if k in BrowserSettings.__annotations__ and k != "proxy"
        }

        if proxy_settings:
            valid_params["proxy"] = proxy_settings

        return BrowserSettings(**valid_params) if valid_params else None

    def _parse_platform_config(
        self, platforms_config: Dict[str, Any]
    ) -> PlatformConfig:
        """Parse platform configurations.

        Args:
            platforms_config: Raw platform configurations

        Returns:
            PlatformConfig object
        """
        platform_settings = {}

        # Parse Feishu platform
        feishu_config = platforms_config.get("feishu", {})
        if feishu_config:
            # Parse TTS config
            tts_config = feishu_config.get("tts") or feishu_config.get("tts_config")
            tts_settings = None
            if tts_config:
                tts_settings = TTSConfig(**tts_config)

            # Create Feishu platform config
            feishu_params = {
                k: v
                for k, v in feishu_config.items()
                if k in FeishuPlatformConfig.__annotations__ and k != "tts"
            }
            if tts_settings:
                feishu_params["tts"] = tts_settings

            if feishu_params:
                platform_settings["feishu"] = FeishuPlatformConfig(**feishu_params)

        return PlatformConfig(**platform_settings)
