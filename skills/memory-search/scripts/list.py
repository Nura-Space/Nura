#!/usr/bin/env python3
"""
Memory list script - List memory files with optional filtering.

Usage:
    python list.py [--limit N] [--type type_name] [--stage stage_name]

Security:
    - Only lists .json files in the memory directory
    - Validates paths to prevent directory traversal
    - Limits output to prevent DoS
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# Security: Maximum number of results to return
MAX_RESULTS = 100


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


def list_memories(
    memory_dir: Path,
    limit: int = MAX_RESULTS,
    type_filter: Optional[str] = None,
    stage_filter: Optional[str] = None,
    show_summary: bool = True
) -> List[Dict[str, Any]]:
    """
    List memory files with optional filtering.

    Args:
        memory_dir: Path to memory directory
        limit: Maximum number of results
        type_filter: Filter by type
        stage_filter: Filter by stage
        show_summary: Include summary in output

    Returns:
        List of memory entries
    """
    results = []
    count = 0

    # Get all JSON files, sorted by name (which includes event number)
    json_files = sorted(memory_dir.glob("event_*.json"))

    for json_file in json_files:
        if not json_file.suffix == ".json":
            continue

        if not json_file.name.startswith("event_"):
            continue

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Apply filters
            if type_filter and data.get("type") != type_filter:
                continue
            if stage_filter and data.get("stage") != stage_filter:
                continue

            entry = {
                "file": json_file.name,
                "type": data.get("type", "unknown"),
                "stage": data.get("stage", "unknown"),
            }

            if show_summary:
                summary = data.get("summary") or data.get("description", "")
                if summary:
                    # Truncate for display
                    entry["summary"] = summary[:100] + "..." if len(summary) > 100 else summary

            results.append(entry)
            count += 1

            if count >= limit:
                break

        except (json.JSONDecodeError, IOError, UnicodeDecodeError):
            continue

    return results


def main():
    parser = argparse.ArgumentParser(
        description="List memory files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python list.py
    python list.py --limit 20
    python list.py --type 日常生活 --stage 凡人
        """
    )

    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=MAX_RESULTS,
        help=f"Maximum number of results (default: {MAX_RESULTS})"
    )

    parser.add_argument(
        "--type", "-t",
        help="Filter by type (e.g., 日常生活, 战斗)"
    )

    parser.add_argument(
        "--stage", "-s",
        help="Filter by stage (e.g., 凡人, 修仙)"
    )

    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Don't show summary in output"
    )

    args = parser.parse_args()

    # Get memory directory
    memory_dir = get_memory_dir()

    if not memory_dir.exists():
        print(f"Error: Memory directory not found: {memory_dir}", file=sys.stderr)
        sys.exit(1)

    # Get list
    results = list_memories(
        memory_dir=memory_dir,
        limit=args.limit,
        type_filter=args.type,
        stage_filter=args.stage,
        show_summary=not args.no_summary
    )

    # Output results
    if not results:
        print("No memory files found.")
        return

    print(f"Found {len(results)} memory entries:")
    print()

    for i, entry in enumerate(results, 1):
        print(f"--- {entry['file']} ---")
        print(f"类型: {entry['type']}")
        print(f"阶段: {entry['stage']}")
        if "summary" in entry:
            print(f"摘要: {entry['summary']}")
        print()


if __name__ == "__main__":
    main()
