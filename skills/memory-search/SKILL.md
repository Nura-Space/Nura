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

## 可搜索字段参考

记忆文件包含以下可搜索字段，用于构造 search/filter 查询条件：

### 核心字段

| 字段 | 含义 | 用途 | 示例查询 |
|------|------|------|----------|
| `type` | 事件类型 | 按事件性质筛选 | `filter type=战斗` |
| `stage` | 修炼阶段 | 时间线定位（重要！） | `filter stage=筑基期` 或 `--sort stage` |
| `location` | 事件地点 | 空间定位 | `filter location=黄枫谷` |
| `emotion` | 主角情感 | 情感状态筛选 | `filter emotion=紧张` |
| `summary` | 事件摘要 | 核心内容（关键词搜索） | `search "韩立修炼" --fields summary` |
| `description` | 详细描述 | 完整叙述（关键词搜索） | `search "韩立修炼" --fields description` |
| `characters.name` | 涉及人物 | 按人物筛选（嵌套字段） | `filter "characters.name=韩立"` |
| `thought` | 内心想法 | 主角心理活动 | `search "向往" --fields thought` |
| `actions` | 主角动作 | 行为描述 | `search "闭上双目" --fields actions` |

**注意**：
- ✅ `type`, `stage`, `summary` 几乎总是存在
- ⚠️ 其他字段可能为空（查询结果显示为 `?`）

### 字段枚举值

#### type（事件类型）

**高频类型**（约占 90%）：
- `社交`, `探索`, `战斗`, `修炼`, `遇险`, `思考`, `观察`

**其他类型**：
- `战斗准备`, `决策`, `准备`, `修炼准备`, `行动`, `飞行`, `移动`
- `日常`, `交易`, `日常生活`, `战斗前准备`, `后续处理`, `等待`

**查询示例**：
```bash
filter type=战斗              # 精确匹配
filter "type~战斗|修炼"       # 正则匹配多个类型
filter "type!=日常生活"       # 排除某类型
```

#### stage（修炼阶段）- 时间线

**阶段顺序**（从低到高）：
```
凡人
→ 炼气期 (一层, 三层, 五层, 六层, 八层, 九层, 十层, 十一层, 十二层, 十三层)
→ 筑基期 (初期, 中期, 后期)
→ 结丹期 (初期, 中期, 后期)
→ 元婴期 (初期, 中期, 后期)
```

**查询示例**：
```bash
filter stage=筑基期           # 模糊匹配（包含"筑基期"的所有阶段）
filter stage=筑基中期         # 精确匹配
list --sort stage             # 按时间线排序（重要！）
list --sort -stage            # 倒序（从高到低）
```

#### emotion（情感状态）

**高频情感**（约占 80%）：
- `平静`, `冷静`, `无奈`, `惊讶`, `疑惑`, `警惕`, `紧张`, `好奇`
- `谨慎`, `兴奋`, `淡定`, `期待`, `满意`, `震惊`, `郁闷`, `轻松`

**其他情感**：
- `严肃`, `惊喜`, `愤怒`, `坚定`, `吃惊`, `专注`, `诧异`, `自信`
- `从容`, `镇定`, `惊恐`, `冷漠`, `犹豫`, `困惑`

**查询示例**：
```bash
filter emotion=紧张           # 查找紧张时刻
filter "emotion~紧张|惊恐"    # 查找多种情感
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
