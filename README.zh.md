# Nura - 通用事件驱动 AI Agent 平台

<div align="center">

[English](README.md) | [简体中文](README.zh.md)

[![CI](https://github.com/baikai-li/nura/actions/workflows/ci.yml/badge.svg)](https://github.com/baikai-li/nura/actions)
[![codecov](https://codecov.io/gh/baikai-li/nura/branch/main/graph/badge.svg)](https://codecov.io/gh/baikai-li/nura)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

Nura 是一个生产级的事件驱动 AI Agent 平台，专为构建智能、可扩展的对话式 AI 应用而设计。拥有约 12k 行 Python 代码，提供了一个完整的框架，用于创建可在多个平台上交互的 AI Agent。

## 🌟 核心特性

### 🎯 核心能力

- **事件驱动架构** - 双优先级队列（主/后台），智能防抖动批处理
- **智能上下文管理** - 50% 阈值自动token优化，基于对话轮次的压缩摘要
- **类型安全配置** - 基于 Pydantic 的统一配置系统，4层配置合并（代码默认值 → 文件 → 环境变量 → 运行时）
- **多提供商 LLM 支持** - OpenAI、Azure、AWS Bedrock、Ark（火山引擎），支持智能缓存
- **动态工具系统** - 可扩展的工具框架，支持自动发现和验证
- **YAML 技能系统** - 使用简单的 YAML 文件定义复杂工作流，支持渐进式披露

### 🤖 Agent 系统

支持多种 Agent 类型，适用于不同场景：

- **BaseAgent** - 基础 Agent，具备状态管理（空闲、运行中、完成、错误）
- **ReActAgent** - 推理与行动，支持思维链
- **ToolCallAgent** - 专门用于工具执行工作流
- **Manus** - 通用任务处理
- **EventDrivenAgent** - 异步事件驱动工作流

### 🔌 平台集成

- **飞书（Lark）** - 全功能 WebSocket 机器人，支持文本、音频、文件消息、表情符号和 TTS
- **可扩展设计** - 易于添加微信、Slack、Discord、Telegram 集成

## 🚀 快速开始

### 前置要求

- Python 3.12 或更高版本
- [uv](https://github.com/astral-sh/uv)（推荐）或 pip

### 安装

```bash
# 克隆仓库
git clone https://github.com/baikai-li/nura.git
cd nura

# 使用 uv 安装（推荐）
uv pip install -e ".[all]"

# 或使用 pip 安装
pip install -e ".[all]"
```

### 基础配置

1. **复制配置模板**：
   ```bash
   cp config/default.example.toml config/default.toml
   cp .env.example .env
   ```

2. **编辑 `.env` 文件，填入你的凭证**：
   ```bash
   # LLM 配置
   NURA_LLM_API_KEY=your-openai-api-key
   NURA_LLM_MODEL=gpt-4

   # 飞书集成配置
   FEISHU_APP_ID=cli_xxx
   FEISHU_APP_SECRET=secret_xxx
   ```

3. **自定义 `config/default.toml`** 进行高级设置

### 运行飞书机器人

```bash
# 进入示例目录
cd examples/feishu_bot

# 使用新配置系统运行
python run.py

# 或使用旧版 JSON 配置运行
python run.py --legacy
```

## 📚 架构设计

### 系统概览

```
┌─────────────────┐
│   用户输入      │
└────────┬────────┘
         ↓
┌────────────────────────────────────┐
│         事件队列                   │
│  ┌──────────┐    ┌──────────┐    │
│  │   主要   │    │  后台    │    │
│  │  优先级  │    │  优先级  │    │
│  └──────────┘    └──────────┘    │
└────────┬───────────────────────────┘
         ↓
    ┌─────────┐
    │ 防抖动  │ (批量处理相似事件)
    └────┬────┘
         ↓
┌──────────────────────┐
│  事件驱动 Agent      │
│  ┌───────────────┐   │
│  │ 上下文管理器  │   │ ← 50% 阈值自动压缩
│  └───────────────┘   │
│  ┌───────────────┐   │
│  │  工具执行器   │   │
│  └───────────────┘   │
└────────┬─────────────┘
         ↓
    ┌────────┐
    │  LLM   │ (OpenAI/Azure/Bedrock/Ark)
    └────┬───┘
         ↓
┌──────────────────────┐
│   消息服务           │
└────────┬─────────────┘
         ↓
┌─────────────────────┐
│   平台输出          │
│ (飞书/Slack/等)     │
└─────────────────────┘
```

### 目录结构

```
nura/
├── agent/           # Agent 实现（BaseAgent、ReAct、ToolCall、Manus）
├── config/          # 统一配置系统
├── context/         # Token 优化的上下文管理
├── core/            # 核心模式、异常、工具
├── event/           # 事件驱动系统（双优先级队列）
├── integrations/    # 平台集成（飞书等）
├── llm/             # LLM 抽象层（支持缓存）
├── prompts/         # Agent 系统提示词
├── sandbox/         # 代码执行沙盒
├── services/        # 服务接口（消息、TTS）
├── skill/           # YAML 技能系统
├── tool/            # 动态工具发现和执行
└── utils/           # 共享工具
```

## 🔧 配置系统

Nura 采用现代化的类型安全配置系统：

### 配置层级（优先级：低 → 高）

1. **代码默认值** - Pydantic 模型中的默认值
2. **配置文件** - `config/` 目录中的 TOML 文件
3. **环境变量** - `NURA_*` 前缀的环境变量
4. **运行时覆盖** - 程序化配置

### 使用示例

```python
from nura.config import get_config

# 获取全局配置
config = get_config()
api_key = config.llm["default"].api_key

# 平台特定配置
config = get_config(platform="feishu")
app_id = config.platforms.feishu.app_id

# 测试用（依赖注入）
from nura.config import ConfigManager

manager = ConfigManager()
test_config = manager.load(overrides={
    "context": {"max_tokens": 1000}
})
```

### 环境变量

```bash
# 核心 LLM 配置
NURA_LLM_API_KEY=sk-xxx
NURA_LLM_MODEL=gpt-4
NURA_LLM_BASE_URL=https://api.openai.com/v1

# 上下文管理
NURA_CONTEXT_MAX_TOKENS=128000
NURA_CONTEXT_KEEP_TURNS=10

# 平台配置（飞书）
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=secret_xxx

# TTS（火山引擎）
VOLCENGINE_TTS_TOKEN=token_xxx
```

## 🛠️ 开发

### 运行测试

```bash
# 所有测试
uv run pytest tests/

# 仅单元测试（快速）
uv run pytest tests/unit/ -v -m unit

# 集成测试
uv run pytest tests/integration/ -v -m integration

# 带覆盖率
uv run pytest tests/ --cov=nura --cov-report=html
open htmlcov/index.html
```

### 代码质量

```bash
# 格式化代码
uv run black nura/

# 代码检查
uv run ruff check nura/

# 类型检查（核心模块）
uv run mypy nura/core/ nura/config/
```

### 可选依赖

```bash
# 沙盒执行
uv pip install -e ".[sandbox]"

# AWS Bedrock
uv pip install -e ".[bedrock]"

# 网络搜索
uv pip install -e ".[websearch]"

# 飞书集成
uv pip install -e ".[feishu]"

# 所有功能
uv pip install -e ".[all]"
```

## 📖 使用示例

### 创建简单 Agent

```python
from nura.agent.base import BaseAgent, AgentState
from nura.config import get_config

class MyAgent(BaseAgent):
    async def step(self) -> None:
        """执行一个推理步骤"""
        async with self.state_context(AgentState.RUNNING):
            # 你的 Agent 逻辑
            response = await self.llm_client.ask(
                messages=self.memory,
                temperature=0.7
            )
            self.update_memory("assistant", response.content)

# 初始化并运行
config = get_config()
agent = MyAgent(llm_config=config.llm["default"])
await agent.run()
```

### 创建自定义工具

```python
from nura.tool.base import BaseTool

class WeatherTool(BaseTool):
    name = "get_weather"
    description = "获取指定地点的当前天气"

    async def execute(self, location: str) -> str:
        """获取天气数据"""
        # 你的实现
        return f"{location}的天气：晴朗，22°C"
```

### 事件驱动集成

```python
from nura.event import EventQueue, Event, EventType
from nura.agent.event_driven import EventDrivenAgent

# 创建事件队列
queue = EventQueue()

# 放入事件
queue.put(Event(
    type=EventType.MAIN,
    data={"text": "你好，Agent！"},
    conversation_id="user_123"
))

# Agent 处理事件
agent = EventDrivenAgent(event_queue=queue)
await agent.run()
```

## 🎯 使用场景

- **客户支持机器人** - 多平台 AI 助手，支持上下文感知
- **内部工具** - 为 Slack/飞书/Discord 提供 AI 助手
- **研究助手** - 支持网络搜索和知识检索的 Agent
- **代码助手** - 在沙盒环境中执行代码的 Agent
- **多 Agent 系统** - 协调的 Agent 工作流，支持任务分解

## 🧪 测试覆盖率

当前覆盖率：**60%+**（单元测试 + 集成测试）

```bash
# 生成覆盖率报告
uv run pytest tests/ --cov=nura --cov-report=term-missing

# 在浏览器中查看
uv run pytest tests/ --cov=nura --cov-report=html
open htmlcov/index.html
```

## 🤝 贡献

我们欢迎贡献！请遵循以下步骤：

1. **Fork** 仓库
2. **创建** 功能分支 (`git checkout -b feature/amazing-feature`)
3. **提交** 更改，使用清晰的提交信息
4. **添加** 新功能的测试（保持 60%+ 覆盖率）
5. **确保** 所有测试通过 (`uv run pytest tests/`)
6. **推送** 到你的分支 (`git push origin feature/amazing-feature`)
7. **创建** Pull Request

### 开发指南

- 使用 `uv` 进行依赖管理
- 遵循 PEP 8 代码风格
- 为所有公共 API 添加类型提示
- 为公共类/方法编写文档字符串
- 保持函数简洁（<50 行）
- 为新功能更新文档

## 📋 路线图

- [ ] Discord 集成
- [ ] Telegram 集成
- [ ] 微信集成
- [ ] Slack 集成
- [ ] 流式响应支持
- [ ] 向量数据库集成
- [ ] 高级记忆系统
- [ ] 多 Agent 编排 UI

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- **OpenManus** - Agent 和工具框架的灵感来源
- **Anthropic** - Claude API 集成模式
- **Volcengine** - Ark LLM 缓存策略

## 📞 支持

- **问题反馈**：[GitHub Issues](https://github.com/baikai-li/nura/issues)
- **讨论交流**：[GitHub Discussions](https://github.com/baikai-li/nura/discussions)
- **开发文档**：查看 [CLAUDE.md](CLAUDE.md) 了解详细开发指南

## 🌐 相关项目

- [OpenManus](https://github.com/OpenBMB/OpenManus) - 开源 Agent 框架
- [LangChain](https://github.com/langchain-ai/langchain) - 使用 LLM 构建应用
- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) - 自主 AI Agent

---

<div align="center">

**由 Nura 团队用 ❤️ 构建**

[English](README.md) | [简体中文](README.zh.md)

</div>
