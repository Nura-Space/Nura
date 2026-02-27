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

复制示例配置文件并填写您的凭证：

```bash
cd examples/feishu_bot
cp config.example.json config.json
# 编辑 config.json 填入您的飞书凭证
```

### 2. 配置说明

`config.json` 参数：

```json
{
  "feishu_app_id": "您的飞书应用ID",
  "feishu_app_secret": "您的飞书应用密钥",
  "profile_path": "profiles/default.yaml",  // 虚拟人设文件
  "memory_dir": "memory",                    // 记忆文件目录
  "enable_voice_reply": false,               // 是否启用语音回复
  "tts_config": {                            // TTS配置（如启用语音）
    "access_token": "字节跳火山引擎Token",
    "app_id": "火山引擎应用ID",
    "cluster": "volcano_tts",
    "voice_type": "zh_female_qingxin"
  }
}
```

### 3. 运行

```bash
# 方式 1：使用 run.py
python run.py

# 方式 2：使用 Nura CLI（从项目根目录）
cd ../..
nura run --config examples/feishu_bot/config.json --platform feishu
```

## 目录结构

```
feishu_bot/
├── config.example.json    # 配置示例
├── config.json            # 实际配置（需自行创建）
├── run.py                 # 启动脚本
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
- 检查 `config/config.toml` 中的 API key 配置
- 查看日志了解具体错误

### 语音回复不工作
- 确认 `enable_voice_reply: true`
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

在 `run.py` 中添加：

```python
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="DEBUG")
```

## 更多信息

- [Nura 文档](../../README.md)
- [飞书开放平台](https://open.feishu.cn/)
- [字节跳火山引擎](https://www.volcengine.com/)
