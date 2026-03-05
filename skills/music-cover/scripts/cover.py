#!/usr/bin/env python3
"""Music Cover CLI - 启动翻唱任务"""

import argparse
import os
import sys
from pathlib import Path

import httpx
from loguru import logger

REPLAY_HOST = os.environ.get("REPLAY_HOST", "localhost")
REPLAY_PORT = os.environ.get("REPLAY_PORT", "62362")
BASE_URL = f"http://{REPLAY_HOST}:{REPLAY_PORT}"
MUSIC_LIBRARY = os.environ.get("MUSIC_LIBRARY")

JOB_FILE = "/tmp/music_cover_job_id"
SONG_FILE = "/tmp/music_cover_song"

MODELS = {"韩立": "hanli"}

# 输出到 stdout 避免被 bash 工具标记为 error
logger.remove()
logger.add(sys.stdout, format="{message}", level="INFO")

transport = httpx.HTTPTransport(local_address="0.0.0.0")


def main():
    parser = argparse.ArgumentParser(description="启动翻唱任务")
    parser.add_argument("--song", "-s", required=True, help="歌曲名称")
    parser.add_argument("--pitch", "-p", type=int, default=0, help="音高调整")
    args = parser.parse_args()

    if not MUSIC_LIBRARY:
        logger.error("请设置环境变量 MUSIC_LIBRARY")
        sys.exit(1)

    # 检查歌曲目录
    song_path = Path(MUSIC_LIBRARY) / args.song
    if not song_path.is_dir():
        logger.error(f"歌曲目录不存在: {song_path}")
        sys.exit(1)

    vocal_path = song_path / "vocal.wav"
    if not vocal_path.exists():
        logger.error("缺少 vocal.wav")
        sys.exit(1)

    # 健康检查
    client = httpx.Client(timeout=30.0, transport=transport)
    try:
        resp = client.get(f"{BASE_URL}/health")
        if resp.status_code != 200:
            logger.error("Replay 服务器未运行")
            sys.exit(1)
    except Exception as e:
        logger.error(f"无法连接 Replay: {e}")
        sys.exit(1)

    # 模型ID
    name = os.environ.get("VIRTUAL_IP_NAME", "")
    model = MODELS.get(name, "")

    logger.info("启动翻唱任务")
    logger.info(f"歌曲: {args.song}, 模型: {model}, 音高: {args.pitch}")

    # 启动任务
    app_support = os.path.expanduser(
        "~/Library/Application Support/Replay/com.replay.Replay"
    )
    data = {
        "outputDirectory": f"{app_support}/outputs",
        "modelsPath": f"{app_support}/models",
        "weightsPath": f"{app_support}/weights",
        "songUrlOrFilePath": str(vocal_path),
        "modelData": [{"modelId": model, "weight": 1.0}],
        "options": {
            "pitch": args.pitch,
            "f0Method": "rmvpe",
            "indexRatio": 0.75,
            "preStemmed": True,
            "vocalsOnly": False,
            "outputFormat": "wav",
        },
    }

    resp = client.post(f"{BASE_URL}/create_song", json=data)
    result = resp.json()
    job_id = result.get("jobId")

    if not job_id:
        logger.error(f"创建任务失败: {result}")
        sys.exit(1)

    # 保存 job_id 和歌曲名称到临时文件
    with open(JOB_FILE, "w") as f:
        f.write(job_id)
    with open(SONG_FILE, "w") as f:
        f.write(args.song)

    logger.info(f"Job ID: {job_id}")
    client.close()


if __name__ == "__main__":
    main()
