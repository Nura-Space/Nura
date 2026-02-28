#!/usr/bin/env python3
"""
Memory read script - Read specific memory file content.

Usage:
    python read.py <event_XXXXX.json>

Security:
    - Only reads .json files in the memory directory
    - Validates filename format (event_XXXXX.json)
    - Validates path to prevent directory traversal
    - Sanitizes output
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional


# Security: Valid filename pattern
FILENAME_PATTERN = re.compile(r'^event_\d+\.json$')


def get_memory_dir() -> Path:
    """Get memory directory from environment or config."""
    memory_dir = os.environ.get("MEMORY_DIR")
    if not memory_dir:
        try:
            from nura.core.config import config
            if config.memory_config and config.memory_config.memory_dir:
                memory_dir = config.memory_config.memory_dir
        except Exception:
            pass

    if not memory_dir:
        print("Error: MEMORY_DIR not set and config not available", file=sys.stderr)
        sys.exit(1)

    return Path(memory_dir).resolve()


def validate_filename(filename: str) -> bool:
    """Validate filename format to prevent path traversal."""
    # Only allow event_XXXXX.json pattern
    if not FILENAME_PATTERN.match(filename):
        return False
    # Additional check: no path separators
    if "/" in filename or "\\" in filename:
        return False
    return True


def validate_path(path: Path, base_dir: Path) -> bool:
    """Validate that path is within base directory (prevent directory traversal)."""
    try:
        resolved = path.resolve()
        return resolved.is_relative_to(base_dir)
    except Exception:
        return False


def read_memory(filename: str, memory_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Read a specific memory file.

    Args:
        filename: Name of the memory file (e.g., event_00001.json)
        memory_dir: Path to memory directory

    Returns:
        Memory content as dict, or None if not found
    """
    # Security: Validate filename
    if not validate_filename(filename):
        print(f"Error: Invalid filename format: {filename}", file=sys.stderr)
        return None

    file_path = memory_dir / filename

    # Security: Validate path
    if not validate_path(file_path, memory_dir):
        print(f"Error: Path traversal attempt detected", file=sys.stderr)
        return None

    if not file_path.exists():
        print(f"Error: File not found: {filename}", file=sys.stderr)
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file: {e}", file=sys.stderr)
        return None
    except (IOError, UnicodeDecodeError) as e:
        print(f"Error: Cannot read file: {e}", file=sys.stderr)
        return None


def format_memory(data: Dict[str, Any], format_json: bool = False) -> str:
    """
    Format memory data for display.

    Args:
        data: Memory content
        format_json: If True, output as JSON; otherwise, format as readable text

    Returns:
        Formatted string
    """
    if format_json:
        return json.dumps(data, ensure_ascii=False, indent=2)

    # Human-readable format
    lines = []

    # Basic fields
    for field in ["type", "stage", "summary", "description"]:
        if field in data and data[field]:
            lines.append(f"{field}: {data[field]}")

    # Actions
    if "actions" in data and data["actions"]:
        lines.append(f"actions: {', '.join(data['actions'])}")

    # Emotion
    if "emotion" in data and data["emotion"]:
        lines.append(f"emotion: {data['emotion']}")

    # Characters
    if "characters" in data and data["characters"]:
        lines.append("\ncharacters:")
        for char in data["characters"]:
            name = char.get("name", "unknown")
            actions = char.get("actions", [])
            emotion = char.get("emotion", "未明确")
            lines.append(f"  - {name}: {', '.join(actions)} (emotion: {emotion})")

    # Prefix/Suffix (context)
    if "prefix" in data and data["prefix"]:
        lines.append(f"\n[prefix]: {data['prefix']}")
    if "suffix" in data and data["suffix"]:
        lines.append(f"[suffix]: {data['suffix']}")

    # Thought/Impact
    if "thought" in data and data["thought"]:
        lines.append(f"\nthought: {data['thought']}")
    if "impact" in data and data["impact"]:
        lines.append(f"impact: {data['impact']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Read specific memory file content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python read.py event_00001.json
    python read.py event_00001.json --json
        """
    )

    parser.add_argument(
        "filename",
        help="Memory file to read (e.g., event_00001.json)"
    )

    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as raw JSON"
    )

    args = parser.parse_args()

    # Get memory directory
    memory_dir = get_memory_dir()

    if not memory_dir.exists():
        print(f"Error: Memory directory not found: {memory_dir}", file=sys.stderr)
        sys.exit(1)

    # Read memory
    data = read_memory(args.filename, memory_dir)

    if data is None:
        sys.exit(1)

    # Output
    print(format_memory(data, format_json=args.json))


if __name__ == "__main__":
    main()
