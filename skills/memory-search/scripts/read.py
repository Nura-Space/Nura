#!/usr/bin/env python3
"""
Memory read script - Read specific memory file content.

Enhanced features:
    - Batch reading: read.py file1.json file2.json file3.json
    - Field selection: read.py file.json --fields summary,type,characters
    - JSON output: read.py file.json --json

Security:
    - Only reads .json files in the memory directory
    - Validates filename format (event_XXXXX.json)
    - Validates path to prevent directory traversal
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Security: Valid filename pattern
FILENAME_PATTERN = re.compile(r"^event_\d+\.json$")


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
    if not FILENAME_PATTERN.match(filename):
        return False
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
    """Read a specific memory file."""
    if not validate_filename(filename):
        print(f"Error: Invalid filename format: {filename}", file=sys.stderr)
        return None

    file_path = memory_dir / filename

    if not validate_path(file_path, memory_dir):
        print("Error: Path traversal attempt detected", file=sys.stderr)
        return None

    if not file_path.exists():
        print(f"Error: File not found: {filename}", file=sys.stderr)
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filename}: {e}", file=sys.stderr)
        return None
    except (IOError, UnicodeDecodeError) as e:
        print(f"Error: Cannot read {filename}: {e}", file=sys.stderr)
        return None


def filter_fields(data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """
    Filter data to only include specified fields.
    Supports dot notation for nested access (e.g., 'characters.name').
    """
    result = {}
    for field in fields:
        if "." in field:
            # Nested field: extract from structure
            parts = field.split(".", 1)
            root, rest = parts[0], parts[1]
            if root in data:
                val = data[root]
                if isinstance(val, list):
                    extracted = []
                    for item in val:
                        if isinstance(item, dict) and rest in item:
                            extracted.append(item[rest])
                    if extracted:
                        result[field] = extracted
                elif isinstance(val, dict) and rest in val:
                    result[field] = val[rest]
        elif field in data:
            result[field] = data[field]
    return result


def is_meaningful_value(value: Any) -> bool:
    """
    Check if a value is meaningful (not empty/unclear/unknown).

    Returns False for:
        - Empty strings, None
        - "未明确", "?", "无" (unclear/unknown indicators)
        - Empty lists/dicts
    """
    if not value:  # None, "", [], {}, 0, False
        return False

    # String indicators of unclear/unknown values
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("未明确", "?", "无", "unknown", "n/a", "null"):
            return False

    return True


def format_memory(data: Dict[str, Any]) -> str:
    """Format memory data for human-readable display."""
    lines = []

    # Basic fields
    for field in ["type", "stage", "summary", "description"]:
        if field in data and is_meaningful_value(data[field]):
            lines.append(f"{field}: {data[field]}")

    # Actions
    if "actions" in data and is_meaningful_value(data["actions"]):
        if isinstance(data["actions"], list):
            lines.append(f"actions: {', '.join(str(a) for a in data['actions'])}")
        else:
            lines.append(f"actions: {data['actions']}")

    # Emotion
    if "emotion" in data and is_meaningful_value(data["emotion"]):
        lines.append(f"emotion: {data['emotion']}")

    # Characters
    if "characters" in data and data["characters"]:
        lines.append("\ncharacters:")
        for char in data["characters"]:
            if isinstance(char, dict):
                name = char.get("name", "unknown")
                actions = char.get("actions", [])
                emotion = char.get("emotion", "")
                action_str = (
                    ", ".join(str(a) for a in actions)
                    if isinstance(actions, list)
                    else str(actions)
                )
                line = f"  - {name}: {action_str}"
                # Only show emotion if it's meaningful
                if is_meaningful_value(emotion):
                    line += f" (emotion: {emotion})"
                lines.append(line)

    # Thought/Impact
    if "thought" in data and is_meaningful_value(data["thought"]):
        lines.append(f"\nthought: {data['thought']}")
    if "impact" in data and is_meaningful_value(data["impact"]):
        lines.append(f"impact: {data['impact']}")

    # Any remaining fields not in the standard set
    standard_fields = {
        "type",
        "stage",
        "summary",
        "description",
        "actions",
        "emotion",
        "characters",
        "thought",
        "impact",
        "location",
        "prefix",  # Skip - not for runtime use
        "suffix",  # Skip - not for runtime use
    }
    for key, value in data.items():
        if key not in standard_fields and value:
            if isinstance(value, (list, dict)):
                lines.append(f"\n{key}: {json.dumps(value, ensure_ascii=False)}")
            else:
                lines.append(f"{key}: {value}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Read memory file content (supports batch reading and field selection)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python read.py event_00001.json
    python read.py event_00001.json event_00002.json event_00003.json
    python read.py event_00001.json --fields summary,type,characters
    python read.py event_00001.json --json
        """,
    )

    parser.add_argument(
        "filenames", nargs="+", help="Memory files to read (e.g., event_00001.json)"
    )
    parser.add_argument("--json", "-j", action="store_true", help="Output as raw JSON")
    parser.add_argument(
        "--fields",
        type=str,
        help="Comma-separated fields to include (e.g., summary,type,characters.name)",
    )

    args = parser.parse_args()

    # Get memory directory
    memory_dir = get_memory_dir()
    if not memory_dir.exists():
        print(f"Error: Memory directory not found: {memory_dir}", file=sys.stderr)
        sys.exit(1)

    # Parse fields
    selected_fields = args.fields.split(",") if args.fields else None

    # Read files
    all_data = []
    errors = 0

    for filename in args.filenames:
        data = read_memory(filename, memory_dir)
        if data is None:
            errors += 1
            continue

        if selected_fields:
            data = filter_fields(data, selected_fields)

        all_data.append((filename, data))

    if not all_data:
        sys.exit(1)

    # Output
    if args.json:
        if len(all_data) == 1:
            print(json.dumps(all_data[0][1], ensure_ascii=False, indent=2))
        else:
            output = [{"file": fn, "data": d} for fn, d in all_data]
            print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for i, (filename, data) in enumerate(all_data):
            if len(all_data) > 1:
                print(f"=== {filename} ===")
            print(format_memory(data))
            if i < len(all_data) - 1:
                print()

    if errors > 0:
        print(f"\n({errors} file(s) could not be read)", file=sys.stderr)


if __name__ == "__main__":
    main()
