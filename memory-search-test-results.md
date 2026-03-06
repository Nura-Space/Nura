# Memory-Search 命令测试结果

生成时间: 2026-03-06 14:27:24

所有命令来自 `skills/memory-search/SKILL.md`

---

## 测试 2: 搜索

### 2.1 关键词搜索
```bash
query.py search "韩立" --limit 3
```

```
Found 3 results (scanned 3713 files):

| ID | Type | Stage | Location | Emotion | Summary |
|---|---|---|---|---|---|
| 0 | 日常生活 | 凡人 | 韩立家中 | 无奈 | 韩立躺在床上，想到自己的绰号和对外面世界的向往，自我安慰 |
| 1 | 日常生活 | 凡人 | 韩立家中 | 向往 | 韩立向往外面世界，睡前想着给妹妹拣红浆果 |
| 2 | 日常生活 | 凡人 | 韩立家中 | 兴奋 | 韩立从山里回家，见到三叔并打招呼 |
```

### 2.2 正则搜索
```bash
query.py search -r "韩立|韩老魔" --limit 3
```

```
Found 3 results (scanned 3713 files):

| ID | Type | Stage | Location | Emotion | Summary |
|---|---|---|---|---|---|
| 0 | 日常生活 | 凡人 | 韩立家中 | 无奈 | 韩立躺在床上，想到自己的绰号和对外面世界的向往，自我安慰 |
| 1 | 日常生活 | 凡人 | 韩立家中 | 向往 | 韩立向往外面世界，睡前想着给妹妹拣红浆果 |
| 2 | 日常生活 | 凡人 | 韩立家中 | 兴奋 | 韩立从山里回家，见到三叔并打招呼 |
```

### 2.3 限定字段搜索
```bash
query.py search "战斗" --fields summary,description --limit 3
```

```
Found 3 results (scanned 3713 files):

| ID | Type | Stage | Location | Emotion | Summary |
|---|---|---|---|---|---|
| 173 | 战斗 | 炼气期六层 | ? | 愤怒、决绝 | 韩立恢复行动能力后与墨大夫对峙，准备战斗 |
| 177 | 战斗 | 炼气期六层 | 房间内 | 冷静且有斗志 | 墨大夫重视韩立，韩立继续靠近准备战斗 |
| 179 | 战斗 | 炼气期六层 | ? | 苦笑、无奈 | 韩立在与墨大夫的战斗中体力透支、左手麻痹，决定动用最后一招 |
```

## 测试 3: 过滤

### 3.1 单条件过滤
```bash
query.py filter type=战斗 --limit 3
```

```
Found 3 results (scanned 3713 files):

| ID | Type | Stage | Location | Emotion | Summary |
|---|---|---|---|---|---|
| 64 | 战斗 | 炼气期三层 | ? | ? | 王大胖击败对手，双方又派出两人持武器继续比试 |
| 72 | 战斗 | 炼气期三层 | ? | ? | 厉师兄与赵子灵进行比试，赵子灵逐渐处于下风 |
| 172 | 战斗（未遂转遇险） | 炼气期六层 | ? | 警觉、后悔 | 墨大夫检测到韩立功力达标后对其出手，韩立疏忽被制 |
```

### 3.2 多条件过滤
```bash
query.py filter type=战斗 stage=筑基期 --limit 3
```

```
No results found.
```

### 3.3 按地点过滤
```bash
query.py filter location=黄枫谷 --limit 3
```

```
Found 3 results (scanned 3713 files):

| ID | Type | Stage | Location | Emotion | Summary |
|---|---|---|---|---|---|
| 586 | 社交 | 炼气期九层 | 黄枫谷大殿 | ? | 介绍黄枫谷掌门钟灵道及大殿内黄枫谷管事人员情况 |
| 587 | 社交 | 炼气期九层 | 黄枫谷大殿 | ? | 叶姓老者与慕容衫就取消其侄孙筑基丹资格给散修一事激烈争辩 |
| 588 | 社交 | 炼气期九层 | 黄枫谷大殿 | ? | 钟灵道呵斥叶姓老者，说明另外两人不能取消筑基丹资格的原因，叶姓老者接受 |
```

### 3.4 按情感过滤
```bash
query.py filter emotion=紧张 --limit 3
```

```
Found 3 results (scanned 3713 files):

| ID | Type | Stage | Location | Emotion | Summary |
|---|---|---|---|---|---|
| 25 | 社交 | 凡人 | 墨大夫房间 | 紧张后放松 | 韩立和张铁见墨大夫，被收为记名弟子，了解相关学习和考核要求 |
| 144 | 遇险 | 炼气期五层 | 彩霞山脉的山林边缘小路旁 | 紧张、警惕 | 韩立在山林中遇到异常，发现两人迎面走来并躲起来偷听 |
| 223 | 遇险 | 炼气期六层 | 石屋门口及附近 | 紧张、担忧 | 韩立发现石门外的铁奴巨汉，意识到自己疏忽了其存在 |
```

### 3.5 正则过滤
```bash
query.py filter "type~战斗|修炼" --limit 3
```

```
Found 3 results (scanned 3713 files):

| ID | Type | Stage | Location | Emotion | Summary |
|---|---|---|---|---|---|
| 29 | 修炼 | 凡人 | ? | 恐惧 | 韩立修炼达到身体承受极限，想起经脉破裂的痛楚而冒冷汗 |
| 31 | 修炼 | 凡人 | ? | ? | 韩立为通过墨大夫考查修炼无名口诀，产生细微凉气真气 |
| 34 | 修炼 | 凡人 | ? | ? | 韩立疯狂修炼，因睡眠不足放弃睡眠中修炼 |
```

## 测试 4: 列表与排序

### 4.1 列出最新事件
```bash
query.py list --limit 3
```

```
Found 3 entries (total 3713 files):

| ID | Type | Stage | Location | Emotion | Summary |
|---|---|---|---|---|---|
| 0 | 日常生活 | 凡人 | 韩立家中 | 无奈 | 韩立躺在床上，想到自己的绰号和对外面世界的向往，自我安慰 |
| 1 | 日常生活 | 凡人 | 韩立家中 | 向往 | 韩立向往外面世界，睡前想着给妹妹拣红浆果 |
| 2 | 日常生活 | 凡人 | 韩立家中 | 兴奋 | 韩立从山里回家，见到三叔并打招呼 |
```

### 4.2 按时间线排序
```bash
query.py list --sort stage --limit 3
```

```
Found 3 entries (total 3713 files):

| ID | Type | Stage | Location | Emotion | Summary |
|---|---|---|---|---|---|
| 1331 | 战斗 | ? | ? | 心里一愣 | 王蝉欲再次困住韩立，因自身中毒情况突变，韩立收走金骷髅头和黄芒 |
| 1560 | ? | ? | ? | 无奈 | 老者明白追踪标记用途后心情复杂 |
| 1556 | 社交 | ? | ? | 平静 | 韩立询问老者所用功法，老者表示不知 |
```

### 4.3 倒序排列（修复后）
```bash
query.py list --sort=-stage --limit 3
```

```
Found 3 entries (total 3713 files):

| ID | Type | Stage | Location | Emotion | Summary |
|---|---|---|---|---|---|
| 3033 | 战斗 | 结丹后期 | ? | ? | 温天仁收回断臂，现身出来 |
| 3121 | 社交 | 结丹后期 | 屋内及屋门口 | 平静 | 韩立告知梅凝去办些事，带着啼魂兽出门 |
| 3064 | 命令与犹豫 | 结丹后期 | 小岛 | ? | 温天仁命令紫灵仙子去抓韩立同伴，紫灵仙子犹豫未行动 |
```

### 4.4 简洁列表
```bash
query.py list --no-summary --limit 3
```

```
Found 3 entries (total 3713 files):

| ID | Type | Stage | Location | Emotion |
|---|---|---|---|---|
| 0 | 日常生活 | 凡人 | 韩立家中 | 无奈 |
| 1 | 日常生活 | 凡人 | 韩立家中 | 向往 |
| 2 | 日常生活 | 凡人 | 韩立家中 | 兴奋 |
```

## 测试 5: 读取详情

### 5.1 读取单个文件
```bash
read.py event_00000.json
```

```
type: 日常生活
stage: 凡人
summary: 韩立躺在床上，想到自己的绰号和对外面世界的向往，自我安慰
description: 韩立躺在床上，身边是酣睡的二哥，听到父母的声音后迫使自己入睡。他被村里人叫“二愣子”，但他并不傻，内心早熟，向往外面的世界，虽不喜欢“二愣子”的称呼，也只能自我安慰。
actions: 缓缓闭上双目, 自我安慰
emotion: 无奈

characters:
  - 韩铸: 酣睡，打呼 (emotion: 未明确)
  - 韩父: 抽旱烟杆 (emotion: 未明确)
  - 韩母: 唠唠叨叨埋怨 (emotion: 未明确)

thought: 向往外面世界，自我安慰不喜欢的绰号
impact: 未明确
```

### 5.2 批量读取
```bash
read.py event_00000.json event_00001.json
```

```
=== event_00000.json ===
type: 日常生活
stage: 凡人
summary: 韩立躺在床上，想到自己的绰号和对外面世界的向往，自我安慰
description: 韩立躺在床上，身边是酣睡的二哥，听到父母的声音后迫使自己入睡。他被村里人叫“二愣子”，但他并不傻，内心早熟，向往外面的世界，虽不喜欢“二愣子”的称呼，也只能自我安慰。
actions: 缓缓闭上双目, 自我安慰
emotion: 无奈

characters:
  - 韩铸: 酣睡，打呼 (emotion: 未明确)
  - 韩父: 抽旱烟杆 (emotion: 未明确)
  - 韩母: 唠唠叨叨埋怨 (emotion: 未明确)

thought: 向往外面世界，自我安慰不喜欢的绰号
impact: 未明确

=== event_00001.json ===
type: 日常生活
stage: 凡人
summary: 韩立向往外面世界，睡前想着给妹妹拣红浆果
description: 韩立内心早熟，向往外面世界，但不敢和人说，迷迷糊糊时想着上山给妹妹拣红浆果。
actions: 迷迷糊糊想事情
emotion: 向往

thought: 向往外面世界，想着给妹妹拣红浆果
impact: 未明确
```

### 5.3 选择字段
```bash
read.py event_00000.json --fields summary,type,emotion
```

```
type: 日常生活
summary: 韩立躺在床上，想到自己的绰号和对外面世界的向往，自我安慰
emotion: 无奈
```

### 5.4 JSON 输出
```bash
read.py event_00000.json --json
```

```json
{
  "type": "日常生活",
  "prefix": "二愣子睁大着双眼，直直望着茅草和烂泥糊成的黑屋顶，身上盖着的旧棉被，已呈深黄色，看不出原来的本来面目，还若有若无的散着淡淡的霉味。",
  "suffix": "韩立虽然并不喜欢这个称呼，但也只能这样一直的自我安慰着。",
  "stage": "凡人",
  "summary": "韩立躺在床上，想到自己的绰号和对外面世界的向往，自我安慰",
  "location": "韩立家中",
  "description": "韩立躺在床上，身边是酣睡的二哥，听到父母的声音后迫使自己入睡。他被村里人叫“二愣子”，但他并不傻，内心早熟，向往外面的世界，虽不喜欢“二愣子”的称呼，也只能自我安慰。",
  "actions": [
    "缓缓闭上双目",
    "自我安慰"
  ],
  "emotion": "无奈",
  "characters": [
    {
      "name": "韩铸",
      "actions": [
        "酣睡，打呼"
      ],
      "emotion": "未明确"
    },
    {
      "name": "韩父",
      "actions": [
        "抽旱烟杆"
      ],
      "emotion": "未明确"
    },
    {
      "name": "韩母",
      "actions": [
        "唠唠叨叨埋怨"
      ],
      "emotion": "未明确"
    }
  ],
  "thought": "向往外面世界，自我安慰不喜欢的绰号",
  "impact": "未明确"
}
```

---

## 测试总结

✅ 所有命令测试完成，包含真实终端输出

