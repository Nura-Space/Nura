#!/usr/bin/env python3
"""轮询翻唱任务状态"""

import os
import shutil
import sys
import time
from pathlib import Path

import httpx
from loguru import logger

REPLAY_HOST = os.environ.get("REPLAY_HOST", "localhost")
REPLAY_PORT = os.environ.get("REPLAY_PORT", "62362")
BASE_URL = f"http://{REPLAY_HOST}:{REPLAY_PORT}"
MUSIC_LIBRARY = os.environ.get("MUSIC_LIBRARY")

JOB_FILE = "/tmp/music_cover_job_id"
SONG_FILE = "/tmp/music_cover_song"

# 输出到 stdout 避免被 bash 工具标记为 error
logger.remove()
logger.add(sys.stdout, format="{message}", level="INFO")

transport = httpx.HTTPTransport(local_address="0.0.0.0")


def main():
    # 从临时文件读取 job_id
    if not os.path.exists(JOB_FILE):
        logger.error("未找到 job_id 文件，请先运行 cover.py")
        sys.exit(1)

    with open(JOB_FILE) as f:
        job_id = f.read().strip()

    # 读取歌曲名称
    song_name = ""
    if os.path.exists(SONG_FILE):
        with open(SONG_FILE) as f:
            song_name = f.read().strip()

    logger.info(f"查询任务: {job_id}")

    # 等待 30 秒避免频繁轮询
    time.sleep(30)

    client = httpx.Client(timeout=60.0, transport=transport)

    try:
        # 第一步: 检查 job 是否在列表中
        resp = client.get(f"{BASE_URL}/jobs")
        jobs = resp.json().get("jobs", [])
        job = next((j for j in jobs if j.get("jobId") == job_id), None)

        if job:
            status = job.get("status", "unknown")
            percent = job.get("percent", 0)
            message = job.get("message", "")
            logger.info(f"status: {status}, progress: {percent/100:.2f}")
            if message:
                logger.info(f"message: {message}")
            
            # 第二步: percent为100时，检查输出目录
            if percent == 100:
                app_support = os.path.expanduser("~/Library/Application Support/Replay/com.replay.Replay")
                job_dir = os.path.join(app_support, "outputs", job_id)

                if os.path.exists(job_dir):
                    final_wav = os.path.join(job_dir, "final.wav")
                    if os.path.exists(final_wav):
                        # 复制到歌曲目录
                        if song_name and MUSIC_LIBRARY:
                            dest_dir = Path(MUSIC_LIBRARY) / song_name
                            dest_path = dest_dir / "cover.wav"
                            shutil.copy(final_wav, dest_path)
                            logger.info(f"status: completed, output: {dest_path}")
                        else:
                            logger.info(f"status: completed, output: {final_wav}")
                        os.remove(JOB_FILE)
                        os.remove(SONG_FILE)
                        client.close()
                        sys.exit(0)

            client.close()
            sys.exit(0)

        logger.warning("status: unknown")
        client.close()
        sys.exit(1)

    except Exception as e:
        logger.error(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
