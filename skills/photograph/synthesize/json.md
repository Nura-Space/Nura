# 资产 JSON Schema

每个资产文件命名为 `asset_*.json`，存放于 `$PHOTO_ASSETS_DIR/`。

## 完整示例

```json
{
  "id": "portrait_001",
  "category": "自画像",
  "path": "/absolute/path/to/image.jpg",
  "description": "身穿青色元婴常服，面容清俊，眼神深邃，单手负后，立于山巅，背景为层层云海与远山。",
  "stage": "元婴期",
  "mood": "威严",
  "location": "灵峰山巅",
  "tags": ["常服", "单手负后", "仙侠写实"],
  "can_reference": true,
  "suitable_for": ["自我介绍", "展示修为", "正式场合"]
}
```

## 字段一览

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 唯一标识，格式建议 `{category_abbr}_{序号}`，如 `portrait_001` |
| `category` | string | ✅ | 资产类别：`自画像` / `居所` / `法器` / `人物` / `场景` |
| `path` | string | ✅ | 图片绝对路径 |
| `description` | string | ✅ | 自然语言描述画面内容，用于全文搜索和生成 prompt（建议 30-100 字） |
| `stage` | string | — | 修炼阶段：`炼气期` / `筑基期` / `结丹期` / `元婴期` |
| `mood` | string | — | 画面氛围：`威严` / `闲适` / `战意` / `温柔` / `肃穆` / `喜悦` |
| `location` | string | — | 拍摄地点，如 `洞府内` / `灵峰山巅` / `宗门广场` |
| `tags` | string[] | — | 补充标签（服饰、动作、视觉风格等） |
| `can_reference` | bool | — | 是否可作为图生图参考图。自画像建议 `true` |
| `suitable_for` | string[] | — | 适用对话场景，如 `["日常聊天", "正式场合"]` |
