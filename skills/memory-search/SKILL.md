---
name: memory-search
description: "记忆检索技能 - 灵活搜索记忆。支持全文搜索、结构化过滤、统计聚合、字段发现等多种查询方式。"
blocking: true
requires:
  env:
    - MEMORY_DIR
---

# 记忆检索技能

## Instructions

灵活搜索和检索记忆目录中的信息。根据查询需求选择最合适的搜索策略。

## 快速参考

| 想做什么 | 命令 |
|----------|------|
| 了解记忆全貌 | `query.py stats` |
| 发现可用字段 | `query.py fields` |
| 关键词搜索 | `query.py search "关键词"` |
| 正则搜索 | `query.py search -r "模式"` |
| 限定字段搜索 | `query.py search "关键词" --fields summary,description` |
| 条件过滤 | `query.py filter field=value` |
| 多条件过滤 | `query.py filter type=战斗 stage=凡人` |
| 嵌套字段过滤 | `query.py filter "characters.name=韩立"` |
| 正则过滤 | `query.py filter "type~战斗\|修炼"` |
| 不等于过滤 | `query.py filter "type!=日常生活"` |
| 分组统计 | `query.py stats --by type,stage` |
| 列出文件 | `query.py list --limit N` |
| 读取详情 | `read.py event_XXXXX.json` |
| 批量读取 | `read.py file1.json file2.json` |
| 选择字段读取 | `read.py event_XXXXX.json --fields summary,type` |

**通用参数** (search/filter/list 共享): `--limit N`, `--offset N`, `--sort FIELD` (倒序用 `--sort="-field"`), `--format detail|compact|json`

## 搜索策略

根据查询需求，选择以下策略之一或组合使用：

### 策略 A: 探索式搜索（不确定目标时）

当不了解记忆内容或结构时，先探索再搜索：

```bash
# 1. 了解记忆总量和分布
python3 ${SKILL_DIR}/scripts/query.py stats

# 2. 了解有哪些可搜索字段
python3 ${SKILL_DIR}/scripts/query.py fields

# 3. 根据发现的信息，用 search 或 filter 缩窄范围
python3 ${SKILL_DIR}/scripts/query.py search "感兴趣的内容"
```

### 策略 B: 关键词搜索（知道要找什么时）

直接用关键词或正则搜索，逐步缩窄：

```bash
# 全文搜索（搜索所有字段）
python3 ${SKILL_DIR}/scripts/query.py search "韩立"

# 正则搜索（支持 .* | 等所有正则语法）
python3 ${SKILL_DIR}/scripts/query.py search -r "韩立|韩老魔"
python3 ${SKILL_DIR}/scripts/query.py search -r "炼气.*筑基"

# 限定搜索字段
python3 ${SKILL_DIR}/scripts/query.py search "战斗" --fields summary,description,actions

# 读取感兴趣的文件
python3 ${SKILL_DIR}/scripts/read.py event_00042.json
```

### 策略 C: 结构化过滤（按条件筛选时）

用精确条件过滤，适合已知字段值的场景：

```bash
# 精确匹配（字符串包含）
python3 ${SKILL_DIR}/scripts/query.py filter type=战斗

# 多条件 AND
python3 ${SKILL_DIR}/scripts/query.py filter type=战斗 stage=凡人

# 正则匹配
python3 ${SKILL_DIR}/scripts/query.py filter "type~战斗|修炼"

# 嵌套字段（dot notation）
python3 ${SKILL_DIR}/scripts/query.py filter "characters.name=韩立"

# 不等于
python3 ${SKILL_DIR}/scripts/query.py filter "type!=日常生活"
```

### 策略 D: 统计分析（需要全局视角时）

用统计了解全局分布，再针对性搜索：

```bash
# 默认按 type 统计
python3 ${SKILL_DIR}/scripts/query.py stats

# 按指定字段统计
python3 ${SKILL_DIR}/scripts/query.py stats --by type
python3 ${SKILL_DIR}/scripts/query.py stats --by stage

# 交叉统计
python3 ${SKILL_DIR}/scripts/query.py stats --by type,stage

# 针对感兴趣的分类深入
python3 ${SKILL_DIR}/scripts/query.py filter type=战斗 --sort="-file" --limit 10
```

## 安全说明

- 只读取 `event_*.json` 格式的文件
- 防止目录遍历攻击
- 结果数量上限 200 条
- 正则编译错误保护

## Examples

```bash
# 探索记忆
python3 ${SKILL_DIR}/scripts/query.py stats
python3 ${SKILL_DIR}/scripts/query.py fields --sample 10

# 搜索
python3 ${SKILL_DIR}/scripts/query.py search "韩立" --limit 10
python3 ${SKILL_DIR}/scripts/query.py search -r "韩立|韩老魔" --format compact
python3 ${SKILL_DIR}/scripts/query.py search "修炼" --fields summary --sort type

# 过滤
python3 ${SKILL_DIR}/scripts/query.py filter type=战斗 stage=凡人
python3 ${SKILL_DIR}/scripts/query.py filter "characters.name=韩立" --format json

# 统计
python3 ${SKILL_DIR}/scripts/query.py stats --by type,stage

# 列出
python3 ${SKILL_DIR}/scripts/query.py list --sort="-file" --limit 10 --offset 20

# 读取详情
python3 ${SKILL_DIR}/scripts/read.py event_00001.json
python3 ${SKILL_DIR}/scripts/read.py event_00001.json event_00002.json --fields summary,type
python3 ${SKILL_DIR}/scripts/read.py event_00001.json --json
```

## 可用脚本

| 脚本 | 用途 | 核心参数 |
|------|------|----------|
| `query.py search` | 全文搜索 | `query`, `-r`, `--fields`, `--context` |
| `query.py filter` | 结构化过滤 | `field=value`, `field~regex`, `field!=value` |
| `query.py stats` | 聚合统计 | `--by field1,field2` |
| `query.py list` | 列出文件 | `--no-summary` |
| `query.py fields` | 发现字段 | `--sample N` |
| `read.py` | 读取文件详情 | `--fields`, `--json`, 支持批量 |
