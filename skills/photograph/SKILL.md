---
name: photograph
description: "拍照技能 - 让数字生命能够在对话中分享照片。根据聊天内容检索图片资产，直接分享或调用 AI 生成新图片后分享给用户。"
blocking: true
requires:
  bins:
    - python3
  env:
    - PHOTO_ASSETS_DIR
    - PHOTO_OUTPUT_DIR
    - ARK_API_KEY
---

# 拍照技能

## Instructions

根据对话上下文，为数字生命提供"拍照"能力：检索图片资产库，判断是直接使用现有图片（Case 1）还是合成新场景（Case 2），最终输出图片路径和对话文本。

---

## 步骤 1：检索图片资产

```bash
# 全文搜索（description + tags 等所有字段）
python3 ${SKILL_DIR}/scripts/query.py search "小绿瓶"
python3 ${SKILL_DIR}/scripts/query.py search "洞府"

# 按 category 过滤
python3 ${SKILL_DIR}/scripts/query.py filter category=居所

# 按修炼阶段过滤
python3 ${SKILL_DIR}/scripts/query.py filter stage=元婴期

# 按氛围过滤（情感对话时）
python3 ${SKILL_DIR}/scripts/query.py filter mood=闲适

# 找可作参考图的素材（Case 2）
python3 ${SKILL_DIR}/scripts/query.py filter can_reference=true

# 组合过滤
python3 ${SKILL_DIR}/scripts/query.py filter category=自画像 stage=元婴期

# 正则过滤多个 category
python3 ${SKILL_DIR}/scripts/query.py filter "category~自画像|法器"

# 列出所有资产 / 发现字段枚举
python3 ${SKILL_DIR}/scripts/query.py list
python3 ${SKILL_DIR}/scripts/query.py fields
```

**输出示例**（`PATH` 列即为图片绝对路径，步骤 3 直接使用）：
```
| ID | CATEGORY | TAGS | PATH | DESCRIPTION |
|---|---|---|---|---|
| item_001 | 法器 | 小绿瓶,灵光 | /db/assets/小绿瓶/item_001.jpg | 通体碧绿发光的圆肚小瓶… |
| portrait_001 | 自画像 | 元婴期,常服 | /db/assets/portraits/portrait_001.jpg | 身穿青色元婴常服，面容清俊… |
```

---

## 步骤 2：判断走 Case 1 还是 Case 2

### Case 1 — 直接使用现有图片

**适用场景**：检索到的图片能直接回应用户需求（如用户问"你家怎么样" → 找到居所图片）。

**操作**：
1. 若结果 > 3 张，随机取 1-3 张
2. 根据图片 description + 聊天上下文，生成对话文本
3. 从 JSON 结果中提取 `path` 字段
4. **按步骤 3 格式输出**：图片路径列表 + 对话文本，然后 terminate

### Case 2 — AI 合成新场景

**适用场景**：需要展示特定动作/场景（如"你平时是怎么斩杀妖兽的"），单张资产无法直接表达。

**操作**：
1. 检索所需素材（自画像 1 张 + 法器/场景若干张）
   - 优先用 `filter category=自画像 can_reference=true`，若无结果则回退到 `filter category=自画像`
2. 用 bash 读取 prompt 技巧文档：
   ```bash
   cat ${SKILL_DIR}/references/prompts.md
   ```
3. 将步骤1的素材描述替换下面这段 `Task` 中的占位符 `{iamge_descroptions}`，然后将完整 Task 输出到终端：

   ```
   ## 图片描述
   {iamge_descroptions}

   ## 任务
   将上述[图片描述]按照上一步的技巧说明，转换成一条完整的参考图生图的prompt，要求：所有要素齐全且满足所有注意事项

   ## 输出
   ```
4. 调用图片生成脚本：
   ```bash
   python3 ${SKILL_DIR}/scripts/generate.py \
     --prompt "生成图片prompt内容" \
     --images "/path/to/portrait.jpg,/path/to/artifact.jpg" \
     --output-dir "${PHOTO_OUTPUT_DIR}"
   ```
5. 生成与图片相应的对话文本
6. **输出**：生成图片路径 + 对话文本

---

## 步骤 3：输出最终总结

在调用 terminate 之前，**必须**用 `bash echo` 输出最终总结，告知主 Agent 图片路径和对话内容。**不能跳过 echo 直接 terminate**，否则图片无法发送给用户。

```bash
echo "拍照完成，请发送给用户，图片文件在 /path/to/img.jpg，对话内容：这是我的洞府……"
```

- 图片路径从步骤 1 检索结果的 PATH 列获取（绝对路径）
- 若有多张图片，echo 中列出所有路径
- 对话内容由 CreateChatCompletion 生成，嵌入 echo 输出中

---

## 资产 Schema

### 字段说明

**必填字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 唯一标识，格式建议 `{category_abbr}_{序号}` |
| `category` | string | 资产类别，见枚举 |
| `path` | string | 图片绝对路径 |
| `description` | string | 自然语言描述画面内容，用于全文搜索和生成 prompt（建议 30-100 字） |

**结构化字段**（可精确 filter，按需填写）

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `stage` | string | 修炼阶段，标记图片拍摄时的境界 | `炼气期` / `筑基期` / `结丹期` / `元婴期` |
| `mood` | string | 画面氛围/情感基调，用于匹配对话情感 | `威严` / `闲适` / `战意` / `温柔` / `肃穆` / `喜悦` |
| `location` | string | 拍摄地点 | `洞府内` / `灵峰山巅` / `宗门广场` / `星海` |
| `tags` | string[] | 补充标签（服饰、动作、视觉风格等零散属性） | `["常服", "御剑", "仙侠写实"]` |

**使用提示字段**（帮助 AI 决策）

| 字段 | 类型 | 说明 |
|------|------|------|
| `can_reference` | bool | 是否可作为 Case 2 图生图的参考图。自画像建议设为 `true`；场景/法器图按需设置 |
| `suitable_for` | string[] | 适用对话场景，帮助 AI 判断何时调用此图 |

**`suitable_for` 常用值**：`自我介绍`、`展示修为`、`展示居所`、`展示法器`、`战斗话题`、`日常聊天`、`正式场合`、`情感互动`

### category 枚举

| 值 | 含义 | `can_reference` 建议 |
|----|------|----------------------|
| `自画像` | 人物本身的图像，含不同服饰/状态/场景 | `true` |
| `居所` | 洞府、修炼室、书房等生活空间 | 按需 |
| `法器` | 飞剑、法宝、阵盘等修炼器物 | `true`（作融合素材）|
| `人物` | 其他人物（友人、弟子、对手等） | 按需 |
| `场景` | 宗门全景、灵地、秘境等环境图 | `true`（作背景素材）|

### 查询示例（基于新字段）

```bash
# 按修炼阶段过滤
python3 ${SKILL_DIR}/scripts/query.py filter stage=元婴期

# 按氛围过滤（情感对话时）
python3 ${SKILL_DIR}/scripts/query.py filter mood=闲适

# 找可作参考图的自画像（Case 2 素材准备）
python3 ${SKILL_DIR}/scripts/query.py filter category=自画像 can_reference=true

# 按适用场景搜索
python3 ${SKILL_DIR}/scripts/query.py search "日常聊天"

# 组合：元婴期 + 可参考
python3 ${SKILL_DIR}/scripts/query.py filter stage=元婴期 can_reference=true
```

---

## 可用脚本

| 脚本 | 用途 | 核心参数 |
|------|------|----------|
| `query.py search` | 全文搜索 description/tags | `keyword` |
| `query.py filter` | 结构化过滤 | `category=居所`, `tags~元婴`, `category!=场景` |
| `query.py list` | 列出所有资产 | `--limit N` |
| `query.py fields` | 发现 category 枚举值 | — |
| `generate.py` | AI 图片生成 | `--prompt`, `--images`, `--output-dir`, `--size` |

**generate.py 完整用法**：
```bash
# 文生图（无参考图）
python3 ${SKILL_DIR}/scripts/generate.py --prompt "..." --output-dir "${PHOTO_OUTPUT_DIR}"

# 多图融合（有参考图）
python3 ${SKILL_DIR}/scripts/generate.py \
  --prompt "参考图1的人物，乘坐图2所示的飞剑，飞越图3的宗门山门" \
  --images "/path/portrait.jpg,/path/sword.jpg,/path/sect.jpg" \
  --output-dir "${PHOTO_OUTPUT_DIR}" \
  --size 2K

# 成功时输出文件路径，失败时输出 ERROR: <message> 并以非零 exit code 退出
```

---

## 安全说明

- `query.py` 只读取 `asset_*.json` 格式的文件，防止目录遍历
- `generate.py` 使用 ARK_API_KEY 调用图片生成 API，输出文件到 PHOTO_OUTPUT_DIR

## Examples

### Case 1 完整示例：用户问"你的洞府是什么样的"

```bash
# 步骤 1：检索，PATH 列即为图片路径
python3 ${SKILL_DIR}/scripts/query.py filter category=居所
# 输出表格含 PATH 列：/db/assets/洞府/01.jpg

# 步骤 2：调用 CreateChatCompletion 生成对话文本（输入：description + 对话上下文）

# 步骤 3：bash echo 输出总结，然后 terminate
echo "拍照完成，请发送给用户，图片文件在 /db/assets/洞府/01.jpg，对话内容：此处便是我的洞府，坐北朝南，灵气充盈，修行多年皆在此地。"
```

### Case 2 完整示例：检索自画像 + 法器合成新场景

```bash
# 步骤 1：并行检索两类资产（自画像优先用 can_reference=true，无结果则去掉该过滤）
python3 ${SKILL_DIR}/scripts/query.py filter category=自画像 can_reference=true
python3 ${SKILL_DIR}/scripts/query.py filter category=法器
# 若自画像 can_reference=true 无结果，再执行：
python3 ${SKILL_DIR}/scripts/query.py filter category=自画像

# 步骤 2：读取 prompt 技巧文档
cat ${SKILL_DIR}/references/prompts.md

# 步骤 3：将步骤 1 检索到的各图片 description（每条换行分隔）填入 Task 占位符，发给 AI 生成图片 prompt
# Task 示例（替换后）：
# ## 图片描述
# [图一]身穿青色元婴常服，面容清俊，右手持剑…
# [图二]通体碧绿发光的圆肚小瓶，悬浮于掌心…
#
# ## 任务
# 将上述[图片描述]按照上一步的技巧说明，转换成一条完整的参考图生图的prompt，要求：所有要素齐全且满足所有注意事项
#
# ## 输出

# 步骤 4：调用 generate.py 生成图片，成功时输出绝对路径，如 /output/generated_001.jpg
python3 ${SKILL_DIR}/scripts/generate.py \
  --prompt "（AI 输出的图片 prompt）" \
  --images "/path/portrait.jpg,/path/artifact.jpg" \
  --output-dir "${PHOTO_OUTPUT_DIR}"

# 步骤 5-6：生成对话文本，bash echo 输出总结，然后 terminate
echo "拍照完成，请发送给用户，图片文件在 /output/generated_001.jpg，对话内容：御剑凌云，宗门山河尽收眼底……"
```
