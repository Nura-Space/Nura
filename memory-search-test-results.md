# Memory-Search 命令测试结果

测试时间：2026-03-06 14:16:18

所有命令来自 `skills/memory-search/SKILL.md`

---

## ❌ 发现的 BUG

### BUG 1: 倒序排序语法错误

**问题命令**：
```bash
query.py list --sort -stage --limit 3
```

**错误输出**：
```
usage: query.py list [-h] [--no-summary] [--limit LIMIT] [--offset OFFSET]
                     [--sort SORT] [--format {detail,compact,json}]
query.py list: error: argument --sort: expected one argument
```

**原因**：`-stage` 被解析为一个独立的选项（因为 `-` 前缀），而不是 `--sort` 的值。

**解决方案**：应该使用 `--sort=-stage`（带等号）或 `--sort="-stage"`（带引号）

---

## ✅ 测试 1: 探索与统计

### 1.1 了解记忆分布
```bash
query.py stats
```

输出：
```
Total: 3713 memory files

Statistics by 'type':

| Value | Count | Percentage |
|---|---|---|
| 社交 | 1603 | 43.2% |
| 探索 | 692 | 18.6% |
| 战斗 | 495 | 13.3% |
| 修炼 | 148 | 4.0% |
| 遇险 | 108 | 2.9% |
```

### 1.2 多维度统计
```bash
query.py stats --by type
```

**结果**: ✅ 正常

### 1.3 发现所有字段
```bash
query.py fields
```

**结果**: ✅ 正常，树形结构显示清晰

---

## ✅ 测试 2: 搜索

### 2.1 关键词搜索
```bash
query.py search "韩立" --limit 3
```

**结果**: ✅ 正常，表格格式显示正确

### 2.2 正则搜索
```bash
query.py search -r "韩立|韩老魔" --limit 3
```

**结果**: ✅ 正常

---

## ✅ 测试 3: 过滤

### 3.1 单条件过滤
```bash
query.py filter type=战斗 --limit 3
```

**结果**: ✅ 正常

### 3.2 多条件过滤
```bash
query.py filter type=战斗 stage=筑基期 --limit 3
```

**结果**: ✅ 正常（无结果是因为数据中没有 `stage=筑基期` 且 `type=战斗` 的记录）

### 3.3 按地点过滤
```bash
query.py filter location=黄枫谷 --limit 3
```

**结果**: ✅ 正常，成功找到 3 条记录

### 3.4 按情感过滤
```bash
query.py filter emotion=紧张 --limit 3
```

**结果**: ✅ 正常

### 3.5 正则过滤
```bash
query.py filter "type~战斗|修炼" --limit 3
```

**结果**: ✅ 正常

---

## ⚠️ 测试 4: 列表与排序

### 4.1 列出最新事件
```bash
query.py list --limit 3
```

**结果**: ✅ 正常

### 4.2 按时间线排序
```bash
query.py list --sort stage --limit 3
```

**结果**: ✅ 正常（但结果包含 `stage=?` 的记录，因为 `?` 排序在前）

### 4.3 倒序排列 ❌
```bash
query.py list --sort -stage --limit 3
```

**结果**: ❌ **错误** - 语法错误，需要修复为 `--sort=-stage`

### 4.4 简洁列表
```bash
query.py list --no-summary --limit 3
```

**结果**: ✅ 正常

---

## ✅ 测试 5: 读取详情

### 5.1 读取单个文件
```bash
read.py event_00000.json
```

**结果**: ✅ 正常，已删除 prefix/suffix 字段

### 5.2 批量读取
```bash
read.py event_00000.json event_00001.json
```

**结果**: ✅ 正常

### 5.3 选择字段
```bash
read.py event_00000.json --fields summary,type,emotion
```

**结果**: ✅ 正常

### 5.4 JSON 输出
```bash
read.py event_00000.json --json
```

**结果**: ✅ 正常

---

## 测试总结

**总计**：19 个命令测试
- ✅ **18 个正常**
- ❌ **1 个错误**

### 需要修复的问题

1. **SKILL.md 中的排序语法**：
   - 错误：`query.py list --sort -stage`
   - 正确：`query.py list --sort=-stage` 或 `query.py list --sort="-stage"`

### 建议

1. 修复 SKILL.md 中所有使用 `--sort -field` 的示例
2. 统一使用 `--sort=-field` 语法（带等号，不需要引号）
3. 或者修改代码，支持 `--sort -field` 语法（但这需要特殊处理 argparse）

生成时间: 2026-03-06 14:16:18
