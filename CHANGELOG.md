# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New configuration system (`nura.config`) with Pydantic models
  - `nura.config` module with `get_config()` function
  - New config models: `LLMSettings`, `ProxySettings`, `SearchSettings`, `MemorySettings`, `MCPSettings`, `SandboxSettings`, `DaytonaSettings`, `RunflowSettings`, `BrowserSettings`
  - Backward compatibility layer in `nura.core.config`
- New LLM cache system with cache factory pattern
  - `nura.llm.cache.base` with `LLMRequestParams` for cache key generation
  - Cache strategy support (`input_only` for ARK cache)
- Request builder pattern in `nura.llm.request` for common request logic

### Changed
- Migrated from `nura.core.config` to `nura.config` for configuration
- Updated `nura.llm.client` to use new configuration and cache systems
- Updated `nura.agent.toolcall` with memory skip logic for special tools with `input_only` caching
- Removed deprecated files: `config/config.example.toml`, `examples/feishu_bot/config.example.json`, `examples/feishu_bot/run.py`
- Updated skill `memory-search` scripts (removed `list.py`, `search.py`, added `query.py`)
- Updated test configurations and coverage settings

### Fixed
- Logger now properly writes to both file and stdout
- Various test improvements and fixes
