---
name: music-cover
description: "翻唱技能 - 将人声转换为虚拟人翻唱声线并混合伴奏。当用户要求生成翻唱、处理歌曲、制作翻唱版本、混合音频轨道时使用。"
requires:
  bins:
    - ffmpeg
    - python3
  env:
    - MUSIC_LIBRARY
    - MUSIC_COVER
always: false
---

# Music Cover - 翻唱技能

## Instructions

使用 Replay 翻唱模型将人声转换为虚拟人的声线，并与伴奏、和声混合生成完整歌曲。

### 环境要求

确保以下环境变量已设置：
- **MUSIC_LIBRARY**: 歌曲库目录
- **MUSIC_COVER**: 输出目录

### 歌曲目录结构

```
${MUSIC_LIBRARY}/
└── {song_name}/
    ├── vocal.wav         # 必需
    ├── accompaniment.wav # 必需
    └── harmony.wav       # 可选
```

### 执行流程

#### 步骤 0: 检查已存在的翻唱文件

首先检查输出目录是否已有翻唱文件，避免重复制作：

```bash
if [ -f "${MUSIC_COVER}/${song_name}_covered_by_${VIRTUAL_IP_NAME}.opus" ]; then
  echo "翻唱文件已存在，请发送给用户: ${MUSIC_COVER}/${song_name}_covered_by_${VIRTUAL_IP_NAME}.opus"
fi
```

如果文件已存在，直接输出文件路径并结束。

#### 步骤 1: 启动任务

```bash
python3 ${SKILL_DIR}/scripts/cover.py \
  --song "${song_name}" \
  --pitch ${pitch_shift}
```

输出示例：`Job ID: abc123...`

#### 步骤 2: 轮询任务状态

重复执行以下命令直到 `status: completed`：

```bash
python3 ${SKILL_DIR}/scripts/wait.py
```

输出示例：
- `status: processing, progress: 0.50` （进行中）
- `status: completed, output: ${MUSIC_LIBRARY}/${song_name}/cover.wav` （已完成）

任务完成后，翻唱文件会自动复制到歌曲目录 `${MUSIC_LIBRARY}/${song_name}/cover.wav`。

#### 步骤 3: 混合音频

```bash
output_file="${MUSIC_COVER}/${song_name}_covered_by_${VIRTUAL_IP_NAME}.opus"

# 构建输入文件参数（使用数组）
inputs=("-i" "${MUSIC_LIBRARY}/${song_name}/cover.wav" "-i" "${MUSIC_LIBRARY}/${song_name}/accompaniment.wav")
if [ -f "${MUSIC_LIBRARY}/${song_name}/harmony.wav" ]; then
  inputs+=("-i" "${MUSIC_LIBRARY}/${song_name}/harmony.wav")
  filter_complex="[0:a]volume=1.2[vocal];[1:a]volume=0.8[acc];[2:a]volume=1.0[harmony];[vocal][acc][harmony]amix=inputs=3:duration=longest[aout]"
else
  filter_complex="[0:a]volume=1.2[vocal];[1:a]volume=0.8[acc];[vocal][acc]amix=inputs=2:duration=longest[aout]"
fi

ffmpeg -y -v quiet "${inputs[@]}" -filter_complex "${filter_complex}" -map "[aout]" -c:a libopus "${output_file}"
[ -f "${output_file}" ] && echo "混音完成"
```

#### 步骤 4: 输出最终总结

在调用 terminate 之前，输出最终总结：

```bash
echo "翻唱完毕，请发送给用户，文件在 ${MUSIC_COVER}/${song_name}_covered_by_${VIRTUAL_IP_NAME}.opus"
```

## Examples

```bash
# 步骤 0: 检查已存在的翻唱文件
if [ -f "${MUSIC_COVER}/晴天_covered_by_韩立.opus" ]; then
  echo "翻唱文件已存在，请发送给用户: ${MUSIC_COVER}/晴天_covered_by_韩立.opus"
fi

# 步骤 1: 启动
python3 ${SKILL_DIR}/scripts/cover.py --song "晴天" --pitch 0
# 输出: Job ID: abc123...

# 步骤 2: 轮询（重复直到完成）
python3 ${SKILL_DIR}/scripts/wait.py
# 重复执行，直到输出包含 "status: completed"

# 步骤 3: 混合
output_file="${MUSIC_COVER}/晴天_covered_by_韩立.opus"

# 构建输入文件参数（使用数组）
inputs=("-i" "${MUSIC_LIBRARY}/晴天/cover.wav" "-i" "${MUSIC_LIBRARY}/晴天/accompaniment.wav")
if [ -f "${MUSIC_LIBRARY}/晴天/harmony.wav" ]; then
  inputs+=("-i" "${MUSIC_LIBRARY}/晴天/harmony.wav")
  filter_complex="[0:a]volume=1.2[vocal];[1:a]volume=0.8[acc];[2:a]volume=1.0[harmony];[vocal][acc][harmony]amix=inputs=3:duration=longest[aout]"
else
  filter_complex="[0:a]volume=1.2[vocal];[1:a]volume=0.8[acc];[vocal][acc]amix=inputs=2:duration=longest[aout]"
fi

ffmpeg -y -v quiet "${inputs[@]}" -filter_complex "${filter_complex}" -map "[aout]" -c:a libopus "${output_file}"
[ -f "${output_file}" ] && echo "混音完成"

# 步骤 4: 输出最终总结
echo "翻唱完毕，请发送给用户，文件在 ${MUSIC_COVER}/晴天_covered_by_韩立.opus"
```
