# Feishu Bot Example

这是一个基于 Nura 的飞书聊天机器人示例。

## 功能特性

- ✅ 事件驱动架构（双优先级队列）
- ✅ 上下文自动压缩（50% token 阈值）
- ✅ 工具调用（记忆搜索、网页搜索、任务规划等）
- ✅ Skill 系统支持
- ✅ TTS 语音回复（可选）
- ✅ Emoji 表情支持

## 快速开始

### 1. 配置

```bash
# 从项目根目录
cd /path/to/Nura

# 1. 复制配置模板
cp config/default.example.toml config/default.toml
cp config/platforms/feishu.example.toml config/platforms/feishu.toml
cp .env.example .env

# 2. 编辑配置文件，填入您的凭证
vim .env
vim config/platforms/feishu.toml
```

**`.env` 文件示例**：
```bash
# 飞书凭证
FEISHU_APP_ID=cli_xxxxxxxxxxxxx
FEISHU_APP_SECRET=your_feishu_app_secret

# TTS 配置（可选，启用语音回复时需要）
VOLCENGINE_TTS_TOKEN=your_volcengine_access_token
VOLCENGINE_TTS_APP_ID=your_volcengine_app_id

# LLM 配置
NURA_LLM_API_KEY=your-api-key
NURA_LLM_MODEL=gpt-4
```

**`config/platforms/feishu.toml` 配置项**：
```toml
# 飞书应用凭证
app_id = "cli_xxxxxxxxxxxxx"
app_secret = "your_feishu_app_secret"

# Agent 人格配置
profile_path = "profiles/assistant.yaml"

# 记忆存储
memory_dir = "examples/feishu_bot/memory"

# 语音回复
enable_voice_reply = false

# 消息收集时间
message_collect_seconds = 10

# TTS 配置
[tts]
access_token = "your_volcengine_access_token"
app_id = "your_volcengine_app_id"
cluster = "volcano_tts"
voice_type = "zh_female_qingxin"
```

### 2. 运行

```bash
# 方式 1：使用 Makefile（从项目根目录）
make run

# 方式 2：使用 Nura CLI
nura run --platform feishu
```

## 目录结构

```
feishu_bot/
├── profiles/              # 虚拟人设
│   └── default.yaml       # 默认人设
├── skills/                # 自定义技能
└── memory/                # 记忆文件（运行时创建）
```

## 虚拟人设配置

编辑 `profiles/default.yaml` 自定义机器人人格：

```yaml
name: "小助手"
language: "zh"
description: "一个友好、专业的AI助手"
style: "友好、专业、简洁"
world: "现代社会"
relations: "用户的贴心助手"
notes: "始终保持礼貌和耐心"
```

## 可用工具

机器人默认配置以下工具：

1. **end_chat**: 结束对话
2. **memory_search**: 搜索本地记忆文件
3. **send_message**: 发送消息（支持emoji和TTS）
4. **send_file**: 发送文件
5. **web_search**: 网页搜索（需要配置搜索引擎）
6. **task_planning**: 复杂任务规划（使用PlanningFlow）
7. **skills**: 执行自定义技能

## 自定义技能

在 `skills/` 目录下创建 YAML 文件定义自定义技能：

```yaml
# skills/example.yaml
name: example_skill
description: "示例技能"
command: "echo 'Hello from skill'"
requires:
  bins: ["echo"]
```

## 故障排查

### 连接失败
- 检查飞书凭证是否正确
- 确认网络连接正常

### 工具调用失败
- 检查 `config/default.toml` 或 `.env` 文件中的 API key 配置
- 确认环境变量已正确设置（`env | grep NURA`）
- 查看日志了解具体错误

### 语音回复不工作
- 确认 `enable_voice_reply = true` 在 feishu.toml 中
- 检查 TTS 配置是否正确
- 确保安装了 `ffmpeg`（用于音频转换）

## 开发调试

### 查看日志

日志会输出到控制台，包含：
- 事件队列状态
- Agent 思考过程
- 工具调用详情
- 错误信息

### 修改日志级别

在代码中添加：

```python
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="DEBUG")
```

## 更多信息

- [Nura 文档](../../README.md)
- [飞书开放平台](https://open.feishu.cn/)
- [字节跳火山引擎](https://www.volcengine.com/)
