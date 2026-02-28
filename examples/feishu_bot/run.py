#!/usr/bin/env python3
"""
Feishu Bot Example for Nura

Usage:
    python run.py
"""
import asyncio
import json
import os
import sys

# Add parent directory to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from nura.integrations.feishu.bot import run_feishu_bot


def main():
    # Load config
    config_path = os.path.join(os.path.dirname(__file__), "config.json")

    if not os.path.exists(config_path):
        print(f"Error: config.json not found at {config_path}")
        print("Please copy config.example.json to config.json and fill in your credentials")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    # Run bot
    asyncio.run(run_feishu_bot(config))


if __name__ == "__main__":
    main()
