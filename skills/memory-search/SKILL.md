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

## 记忆文件 Schema

每个记忆文件 (`event_XXXXX.json`) 包含以下结构化信息：

### 字段定义

| 字段 | 类型 | 必需 | 描述 | 示例 |
|------|------|------|------|------|
| `type` | string (enum) | ✅ | 事件类型 | `社交`, `探索`, `战斗`, `修炼` |
| `stage` | string (enum) | ✅ | 修炼阶段（时间线定位） | `凡人`, `炼气期`, `筑基期`, `结丹期`, `元婴期` |
| `summary` | string | ✅ | 事件摘要（核心内容） | `韩立躺在床上，想到...` |
| `location` | string | ⭐ | 事件地点（空间定位） | `韩立家中`, `黄枫谷`, `青牛镇` |
| `emotion` | string (enum) | ⭐ | 主角情感状态 | `平静`, `紧张`, `兴奋`, `无奈` |
| `description` | string | ⭐ | 详细描述（比 summary 更长） | `韩立躺在床上，身边是酣睡的...` |
| `thought` | string | ⭐ | 主角内心想法 | `向往外面世界，自我安慰...` |
| `actions` | array[string] | ⭐ | 主角动作列表 | `["缓缓闭上双目", "自我安慰"]` |
| `characters` | array[object] | ⭐ | 涉及人物列表 | 见下方嵌套结构 |
| `impact` | string | ⭐ | 事件影响 | `未明确`, `获得修炼资源` |

**注**：✅ = 几乎总是存在，⭐ = 可能缺失（显示为 `?`）

### 嵌套结构：characters

```json
{
  "name": "string",      // 人物名称，如 "韩立", "李化元"
  "actions": ["string"], // 人物动作列表
  "emotion": "string"    // 人物情感，如 "平静", "愤怒"
}
```

### 枚举值参考

#### type (事件类型) - 前 20 个高频值
```
社交      探索      战斗      修炼      遇险      思考      观察
战斗准备  决策      准备      修炼准备  行动      飞行      移动
日常      交易      日常生活  战斗前准备  后续处理  等待
```

#### stage (修炼阶段) - 按修炼进度排序
```
凡人 → 炼气期(一~十三层) → 筑基期(初/中/后期) → 结丹期(初/中/后期) → 元婴期(初/中/后期)
```

常见具体值：
```
凡人, 炼气期一层, 炼气期三层, 炼气期五层, 炼气期六层, 炼气期八层,
炼气期九层, 炼气期十层, 炼气期十一层, 炼气期十二层, 炼气期十三层,
筑基初期, 筑基中期, 筑基后期, 结丹初期, 结丹中期, 结丹后期,
元婴初期, 元婴中期, 元婴后期
```

#### emotion (情感状态) - 前 30 个高频值
```
平静    冷静    无奈    惊讶    疑惑    警惕    紧张    好奇
谨慎    兴奋    淡定    期待    满意    震惊    郁闷    轻松
严肃    惊喜    愤怒    坚定    吃惊    专注    诧异    自信
从容    镇定    惊恐    冷漠    犹豫    困惑
```

### 完整示例

```json
{
  "type": "日常生活",
  "stage": "凡人",
  "summary": "韩立躺在床上，想到自己的绰号和对外面世界的向往，自我安慰",
  "location": "韩立家中",
  "emotion": "无奈",
  "description": "韩立躺在床上，身边是酣睡的二哥，听到父母的声音后迫使自己入睡。他被村里人叫"二愣子"，但他并不傻，内心早熟，向往外面的世界，虽不喜欢"二愣子"的称呼，也只能自我安慰。",
  "actions": ["缓缓闭上双目", "自我安慰"],
  "thought": "向往外面世界，自我安慰不喜欢的绰号",
  "impact": "未明确",
  "characters": [
    {
      "name": "韩铸",
      "actions": ["酣睡，打呼"],
      "emotion": "未明确"
    },
    {
      "name": "韩父",
      "actions": ["抽旱烟杆"],
      "emotion": "未明确"
    }
  ]
}
```

## 快速参考

| 想做什么 | 命令 |
|----------|------|
| **探索与统计** | |
| 了解记忆分布 | `query.py stats` (按 type 统计) |
| 多维度统计 | `query.py stats --by type,stage,emotion` |
| 发现所有字段 | `query.py fields` |
| **搜索** | |
| 关键词搜索 | `query.py search "关键词"` |
| 正则搜索 | `query.py search -r "韩立\|韩老魔"` |
| 限定字段搜索 | `query.py search "战斗" --fields summary,description` |
| **过滤** | |
| 单条件过滤 | `query.py filter type=战斗` |
| 多条件过滤 | `query.py filter type=战斗 stage=筑基期` |
| 按地点过滤 | `query.py filter location=黄枫谷` |
| 按情感过滤 | `query.py filter emotion=紧张` |
| 嵌套字段过滤 | `query.py filter "characters.name=韩立"` |
| 正则过滤 | `query.py filter "type~战斗\|修炼"` |
| 排除过滤 | `query.py filter "type!=日常生活"` |
| **列表与排序** | |
| 列出最新事件 | `query.py list --limit 10` |
| 按时间线排序 | `query.py list --sort stage` |
| 倒序排列 | `query.py list --sort -stage` (前缀 `-` 表示倒序) |
| 简洁列表 | `query.py list --no-summary` |
| **读取详情** | |
| 读取单个文件 | `read.py event_00042.json` |
| 批量读取 | `read.py event_00042.json event_00043.json` |
| 选择字段 | `read.py event_00042.json --fields summary,type,emotion` |
| JSON 输出 | `read.py event_00042.json --json` |

**通用参数** (search/filter/list 共享):
- `--limit N` - 限制结果数量（默认 50，最大 200）
- `--offset N` - 跳过前 N 个结果（分页）
- `--sort FIELD` - 按字段排序（倒序用 `-FIELD`，如 `--sort -stage`）
- `--format FORMAT` - 输出格式：
  - `compact` (默认) - 表格格式，紧凑高效
  - `detail` - 详细文本格式
  - `json` - JSON 格式，程序化使用

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
