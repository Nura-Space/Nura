"""Pydantic configuration models for Nura.

This module defines all configuration models with type safety and validation.
"""

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================================
# Core Configuration Models
# ============================================================================


class LLMSettings(BaseModel):
    """LLM provider configuration."""

    model: str = Field(..., description="Model name")
    base_url: str = Field(..., description="API base URL")
    api_key: str = Field(..., description="API key")
    max_tokens: int = Field(4096, description="Maximum number of tokens per request")
    max_input_tokens: Optional[int] = Field(
        None,
        description="Maximum input tokens to use across all requests (None for unlimited)",
    )
    temperature: float = Field(1.0, description="Sampling temperature")
    api_type: str = Field("", description="Azure, Openai, or Ollama")
    api_version: str = Field("", description="Azure Openai version if AzureOpenai")
    cache_ttl: int = Field(3600, description="Cache TTL in seconds")
    cache_strategy: str = Field(
        "input_only",
        description="Cache strategy: 'full' (cache input + output) or 'input_only' (cache input only)",
    )


class ContextConfig(BaseModel):
    """Configuration for context management (turn-based compression).

    New turn-based compression scheme:
    - Trigger threshold: 50% token (64000 for 128000 context)
    - Keep recent 10 conversation turns (not messages)
    - Compress everything before the 10th turn using LLM summarization
    """

    # Context window size
    max_tokens: int = Field(128000, description="Maximum context window size")

    # Compress when token count reaches this threshold (0.5 = 50%)
    compress_threshold: float = Field(
        0.5, description="Compress when token count reaches this ratio (0.5 = 50%)"
    )

    # Keep recent N conversation turns
    keep_turns: int = Field(10, description="Number of recent conversation turns to keep")

    # Minimum seconds between compressions
    compress_cooldown: int = Field(
        60, description="Minimum seconds between compressions"
    )

    @property
    def compress_tokens(self) -> int:
        """Trigger compression when token count reaches this (max_tokens * compress_threshold)"""
        return int(self.max_tokens * self.compress_threshold)


class MemorySettings(BaseModel):
    """Memory storage configuration."""

    memory_dir: Optional[str] = Field(None, description="Directory for memory storage")


class CoreSettings(BaseModel):
    """Core project settings."""

    project_root: Optional[Path] = Field(None, description="Project root directory")
    workspace_root: Optional[Path] = Field(None, description="Workspace root directory")


# ============================================================================
# Feature Configuration Models
# ============================================================================


class ProxySettings(BaseModel):
    """Proxy configuration."""

    server: Optional[str] = Field(None, description="Proxy server address")
    username: Optional[str] = Field(None, description="Proxy username")
    password: Optional[str] = Field(None, description="Proxy password")


class BrowserSettings(BaseModel):
    """Browser automation configuration."""

    headless: bool = Field(False, description="Whether to run browser in headless mode")
    disable_security: bool = Field(
        True, description="Disable browser security features"
    )
    extra_chromium_args: List[str] = Field(
        default_factory=list, description="Extra arguments to pass to the browser"
    )
    chrome_instance_path: Optional[str] = Field(
        None, description="Path to a Chrome instance to use"
    )
    wss_url: Optional[str] = Field(
        None, description="Connect to a browser instance via WebSocket"
    )
    cdp_url: Optional[str] = Field(
        None, description="Connect to a browser instance via CDP"
    )
    proxy: Optional[ProxySettings] = Field(
        None, description="Proxy settings for the browser"
    )
    max_content_length: int = Field(
        2000, description="Maximum length for content retrieval operations"
    )


class SandboxSettings(BaseModel):
    """Configuration for the execution sandbox."""

    use_sandbox: bool = Field(False, description="Whether to use the sandbox")
    image: str = Field("python:3.12-slim", description="Base image")
    work_dir: str = Field("/workspace", description="Container working directory")
    memory_limit: str = Field("512m", description="Memory limit")
    cpu_limit: float = Field(1.0, description="CPU limit")
    timeout: int = Field(300, description="Default command timeout (seconds)")
    network_enabled: bool = Field(
        False, description="Whether network access is allowed"
    )


class SearchSettings(BaseModel):
    """Web search configuration."""

    engine: str = Field(default="Google", description="Search engine the llm to use")
    fallback_engines: List[str] = Field(
        default_factory=lambda: ["DuckDuckGo", "Baidu", "Bing"],
        description="Fallback search engines to try if the primary engine fails",
    )
    retry_delay: int = Field(
        default=60,
        description="Seconds to wait before retrying all engines again after they all fail",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of times to retry all engines when all fail",
    )
    lang: str = Field(
        default="en",
        description="Language code for search results (e.g., en, zh, fr)",
    )
    country: str = Field(
        default="us",
        description="Country code for search results (e.g., us, cn, uk)",
    )


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    type: str = Field(..., description="Server connection type (sse or stdio)")
    url: Optional[str] = Field(None, description="Server URL for SSE connections")
    command: Optional[str] = Field(None, description="Command for stdio connections")
    args: List[str] = Field(
        default_factory=list, description="Arguments for stdio command"
    )


class MCPSettings(BaseModel):
    """Configuration for MCP (Model Context Protocol)."""

    server_reference: str = Field(
        "app.mcp.server", description="Module reference for the MCP server"
    )
    servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict, description="MCP server configurations"
    )


class RunflowSettings(BaseModel):
    """Run flow configuration."""

    use_data_analysis_agent: bool = Field(
        default=False, description="Enable data analysis agent in run flow"
    )


class DaytonaSettings(BaseModel):
    """Daytona sandbox configuration."""

    daytona_api_key: Optional[str] = None
    daytona_server_url: Optional[str] = Field(
        "https://app.daytona.io/api", description=""
    )
    daytona_target: Optional[str] = Field("us", description="enum ['eu', 'us']")
    sandbox_image_name: Optional[str] = Field("whitezxj/sandbox:0.1.0", description="")
    sandbox_entrypoint: Optional[str] = Field(
        "/usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf",
        description="",
    )
    VNC_password: Optional[str] = Field(
        "123456", description="VNC password for the vnc service in sandbox"
    )


# ============================================================================
# Platform Configuration Models
# ============================================================================


class TTSConfig(BaseModel):
    """Text-to-Speech configuration."""

    access_token: str = Field(..., description="TTS service access token")
    app_id: str = Field(..., description="TTS app ID")
    cluster: str = Field("volcano_tts", description="TTS cluster name")
    voice_type: str = Field("zh_female_qingxin", description="Voice type")


class FeishuPlatformConfig(BaseModel):
    """Feishu platform configuration."""

    app_id: str = Field(..., description="Feishu app ID")
    app_secret: str = Field(..., description="Feishu app secret")
    profile_path: str = Field(
        "profiles/assistant.yaml",
        description="Path to agent profile YAML file (will be loaded dynamically)",
    )
    memory_dir: Optional[str] = Field(None, description="Memory directory for this platform")
    enable_voice_reply: bool = Field(False, description="Enable voice reply feature")
    message_collect_seconds: int = Field(
        10, description="Seconds to collect messages before processing"
    )
    tts: Optional[TTSConfig] = Field(None, description="TTS configuration")


class PlatformConfig(BaseModel):
    """All platform configurations."""

    feishu: Optional[FeishuPlatformConfig] = Field(
        None, description="Feishu platform configuration"
    )
    # Future: discord, telegram, slack, etc.


# ============================================================================
# Root Configuration Model
# ============================================================================


class NuraConfig(BaseSettings):
    """Root configuration model for Nura.

    This is the main configuration object that combines all settings.
    Supports environment variable overrides with NURA_* prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="NURA_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
    )

    # Core settings
    core: CoreSettings = Field(default_factory=CoreSettings)

    # LLM configurations (supports multiple profiles: default, vision, etc.)
    llm: Dict[str, LLMSettings] = Field(
        default_factory=dict, description="LLM configurations by profile name"
    )

    # Context management
    context: ContextConfig = Field(
        default_factory=ContextConfig, description="Context management configuration"
    )

    # Memory storage
    memory: MemorySettings = Field(
        default_factory=MemorySettings, description="Memory storage configuration"
    )

    # Feature configurations
    browser: Optional[BrowserSettings] = Field(
        None, description="Browser automation configuration"
    )
    sandbox: Optional[SandboxSettings] = Field(
        None, description="Sandbox execution configuration"
    )
    search: Optional[SearchSettings] = Field(
        None, description="Web search configuration"
    )
    mcp: Optional[MCPSettings] = Field(None, description="MCP configuration")
    runflow: Optional[RunflowSettings] = Field(
        None, description="Run flow configuration"
    )
    daytona: Optional[DaytonaSettings] = Field(
        None, description="Daytona configuration"
    )

    # Platform configurations
    platforms: PlatformConfig = Field(
        default_factory=PlatformConfig, description="Platform-specific configurations"
    )
