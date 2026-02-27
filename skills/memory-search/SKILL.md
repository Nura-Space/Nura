---
name: memory-search
description: "记忆检索技能 - 在记忆目录中搜索和检索过去的对话或信息。支持链式检索，通过多轮搜索逐步定位目标记忆。"
blocking: true
requires:
  env:
    - MEMORY_DIR
---

# 记忆检索技能

## Instructions

在记忆目录中搜索和检索过去的对话或信息。这个技能支持链式检索，通过多轮搜索逐步定位目标记忆。

### 环境要求

- **MEMORY_DIR**: 记忆目录路径（从配置中读取）

如果未设置 MEMORY_DIR 环境变量，将使用配置中的 memory.memory_dir。

### 安全说明

本技能使用安全的专用脚本执行操作，所有脚本都包含以下安全措施：
- 只允许读取 .json 文件
- 防止目录遍历攻击
- 限制搜索结果数量防止 DoS
- 输入验证和过滤

### 搜索策略

由于记忆可能分散在多个文件中，建议采用以下链式检索策略：

#### 步骤 1: 了解记忆目录结构

首先列出记忆目录，了解记忆的数量和范围：

```bash
python3 ${SKILL_DIR}/scripts/list.py --limit 20
```

#### 步骤 2: 初步搜索

根据用户的需求进行初步搜索：

```bash
# 简单关键词搜索
python3 ${SKILL_DIR}/scripts/search.py --keyword "关键词"

# 限制结果数量
python3 ${SKILL_DIR}/scripts/search.py --keyword "关键词" --limit 10

# 正则表达式搜索（更强大，支持通配符、交替等）
python3 ${SKILL_DIR}/scripts/search.py --pattern "韩立|韩老魔"
python3 ${SKILL_DIR}/scripts/search.py --pattern "炼气.*筑基" --limit 10

# 在特定字段中搜索
python3 ${SKILL_DIR}/scripts/search.py --keyword "战斗" --field description --field actions

# 使用正则搜索特定字段
python3 ${SKILL_DIR}/scripts/search.py --pattern "炼气|筑基" --field stage

# 区分大小写的正则搜索
python3 ${SKILL_DIR}/scripts/search.py --pattern "韩立" --case-sensitive
```

#### 步骤 3: 评估并优化搜索

根据初步搜索结果的文件名，读取具体文件查看详情：

```bash
# 读取指定文件
python3 ${SKILL_DIR}/scripts/read.py event_00001.json

# 以 JSON 格式输出
python3 ${SKILL_DIR}/scripts/read.py event_00001.json --json
```

#### 步骤 4: 筛选结果

可以使用类型或阶段筛选：

```bash
# 按类型筛选
python3 ${SKILL_DIR}/scripts/list.py --type 日常生活

# 按阶段筛选
python3 ${SKILL_DIR}/scripts/list.py --stage 凡人

# 组合筛选
python3 ${SKILL_DIR}/scripts/list.py --type 战斗 --limit 20
```

### 链式检索流程

1. 首先执行初步搜索（使用 search.py）
2. 评估搜索结果，如果不够精确则进行第二轮搜索
3. 读取感兴趣的文件（使用 read.py）
4. 重复直到找到目标信息
5. 返回结构化的检索结果

### 最终输出

在调用 terminate 之前，输出最终总结：

```bash
echo "=== 记忆检索结果 ==="
python3 ${SKILL_DIR}/scripts/read.py event_00001.json
echo "==================="
```

## Examples

```bash
# 步骤 1: 查看记忆列表
python3 ${SKILL_DIR}/scripts/list.py --limit 20

# 步骤 2: 初步搜索 - 关键词
python3 ${SKILL_DIR}/scripts/search.py --keyword "韩立"

# 步骤 2: 初步搜索 - 正则表达式（更强大）
python3 ${SKILL_DIR}/scripts/search.py --pattern "韩立|韩老魔"
python3 ${SKILL_DIR}/scripts/search.py --pattern "炼气.*筑基"

# 步骤 3: 读取具体文件
python3 ${SKILL_DIR}/scripts/read.py event_00001.json

# 步骤 4: 读取多个文件
python3 ${SKILL_DIR}/scripts/read.py event_00002.json

# 最终输出
echo "=== 记忆检索结果 ==="
python3 ${SKILL_DIR}/scripts/read.py event_00001.json
echo "==================="
```

## 可用脚本

| 脚本 | 用途 | 示例 |
|------|------|------|
| `list.py` | 列出记忆文件 | `python3 list.py --limit 20` |
| `search.py` | 关键词搜索 | `python3 search.py --keyword "韩立"` |
| `search.py` | 正则搜索 | `python3 search.py --pattern "韩立\|韩老魔"` |
| `read.py` | 读取指定文件 | `python3 read.py event_00001.json` |
