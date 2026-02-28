# Nura - Universal Event-Driven AI Agent Platform

Nura is a universal event-driven AI Agent platform that integrates:
- **OpenManus core** (Agent, Tool, Flow, Skill systems)
- **Event-driven architecture** (EventQueue, Context Management)
- **Platform abstraction** (MessagingService, TTSService)
- **Token-optimized context** (50% threshold compression with Ark cache)

## Architecture

```
nura/
├── core/           # Core schemas and utilities (from OpenManus)
├── llm/            # LLM abstraction with Ark cache support
├── tool/           # Tool system (merged OpenManus + Virtual-IP)
├── agent/          # Agent implementations (Base, ReAct, ToolCall, Manus)
├── flow/           # Multi-agent coordination (Planning Flow)
├── skill/          # Skill system (dynamic discovery & execution)
├── event/          # Event-driven system (dual-priority queue)
├── context/        # Token-based context compression (50% threshold)
├── services/       # Service abstractions (Messaging, TTS)
└── integrations/   # Platform plugins (Feishu, WeChat, Slack)
```

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/nura.git
cd nura

# Setup development environment (uses uv)
./setup-dev-env.sh

# Or manual setup with uv
uv pip install -e ".[all]"
```

### Running Feishu Bot Example

```bash
# Configure
cd examples/feishu_bot
cp config.example.json config.json
# Edit config.json with your credentials

# Run (uses uv automatically)
nura run --config examples/feishu_bot/config.json --platform feishu
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only (fast)
make test-unit

# Run with coverage
make test-cov
open htmlcov/index.html

# Run in parallel
make test-parallel
```

Note: All commands use `uv` automatically. Use `uv run pytest` for direct pytest access.

### Test Structure

- `tests/unit/` - Fast, isolated unit tests (70%+ coverage target)
- `tests/integration/` - Multi-module integration tests
- `tests/e2e/` - End-to-end workflow tests
- `tests/fixtures/` - Test data and fixtures
- `tests/helpers/` - Test utilities (mock_llm, poll, temp_dir)

### Code Quality

```bash
# Install dev dependencies
make install-dev

# Format code
black nura/

# Lint
ruff check nura/

# Type check
mypy nura/
```

## Features

### Event-Driven Architecture
- Dual-priority event queue (Main > Background)
- Thread-safe operations
- Debounce support for batch processing
- Conversation-based routing

### Token-Optimized Context
- Automatic compression at 50% threshold
- Preserves recent N messages
- Summarizes older messages
- Transparent LLM integration

### Platform Abstraction
- MessagingService interface (text, file, audio)
- TTSService interface
- Easy to add new platforms (WeChat, Slack, etc.)

### Agent System
- BaseAgent with state management
- ReActAgent for reasoning
- ToolCallAgent for tool execution
- Manus for general tasks
- EventDrivenAgent for async workflows

### Tool System
- Merged OpenManus + Virtual-IP tools
- BaseTool abstraction
- ToolCollection for grouping
- Dynamic tool discovery

### Flow System
- PlanningFlow for task decomposition
- Multi-agent coordination
- Sub-agent spawning

### Skill System
- YAML-based skill definitions
- Dynamic discovery from multiple directories
- Progressive disclosure
- Requires validation (bins, env vars)

## Platform Integrations

### Feishu (Implemented)
- WebSocket bot connection
- Text, audio, file messaging
- Emoji support
- TTS via Volcengine

### Coming Soon
- WeChat integration
- Slack integration
- Discord integration

## Architecture Diagrams

### Event Flow
```
User Message → EventQueue (Main) → EventDrivenAgent → ToolCall → MessagingService → Platform
                      ↓
           Debounce + Batch → Context Compression → LLM (with Ark cache)
```

### Context Compression
```
Messages: [m1, m2, ..., m50, m51, ...]
          ↓ (token count > 50% threshold)
Summary: [Summary of m1-m45] + [m46, m47, ..., m51, ...]
         ↓
To LLM: [system(summary), m46, m47, ..., m51, new_message]
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contribution Guidelines
- Add unit tests for new features
- Maintain 70%+ code coverage
- Follow existing code style
- Update documentation

## Acknowledgments

- **OpenManus** - Core agent and tool framework
- **Virtual-IP** - Event-driven architecture inspiration
- **Anthropic** - Claude API integration

## Support

- GitHub Issues: https://github.com/yourusername/nura/issues
- Documentation: https://nura.readthedocs.io/
