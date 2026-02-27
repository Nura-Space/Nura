"""Emoji support for Feishu integration."""
import json
import os
from loguru import logger


def load_emoji_functions(emoji_path: str = None) -> dict:
    """Load emoji functions from JSON file.

    Args:
        emoji_path: Path to emoji JSON file. If None, tries default locations.

    Returns:
        Dictionary of emoji categories and their emoji strings
    """
    # Try default locations if not specified
    if not emoji_path:
        possible_paths = [
            "bot/asset/emoji.json",
            "examples/feishu_bot/emoji.json",
            "../emoji.json"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                emoji_path = path
                break

    if not emoji_path or not os.path.exists(emoji_path):
        logger.warning("Emoji file not found, emoji support disabled")
        return {}

    try:
        with open(emoji_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            emoji_func = data.get("categories", {})
            logger.info(f"Loaded {len(emoji_func)} emoji categories")
            return emoji_func
    except Exception as e:
        logger.error(f"Failed to load emoji from {emoji_path}: {e}")
        return {}
