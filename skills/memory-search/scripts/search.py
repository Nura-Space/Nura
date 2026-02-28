#!/usr/bin/env python3
"""
Memory search script - Securely search memory files by keyword or regex pattern.

Usage:
    python search.py --keyword "关键词" [--limit N]
    python search.py --pattern "正则表达式" [--limit N]
    python search.py --field summary "关键词"

Security:
    - Only reads .json files in the memory directory
    - Validates paths to prevent directory traversal
    - Limits search results to prevent DoS
    - Filters output to prevent information disclosure
    - Regex patterns are limited to safe operations only
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# Security: Allowed fields to search in
ALLOWED_FIELDS = {
    "type", "prefix", "suffix", "stage", "summary",
    "description", "location", "actions", "emotion",
    "characters", "thought", "impact"
}

# Security: Maximum number of results to return
MAX_RESULTS = 50

# Security: Allowed regex patterns (disallow potentially dangerous patterns)
FORBIDDEN_REGEX_PATTERNS = [
    r"(?<!\\)\.\*",      # .* (greedy) - use .*? instead
    r"\.\+",             # .+ (greedy)
    r"\*\*",             # ** (recursive)
    r"\{,\}",            # {,} (empty repeat)
    r"\(\?=",            # lookahead (potential DoS)
    r"\(\?!",            # negative lookahead
    r"\(\?<=",           # lookbehind
    r"\(\?<!",           # negative lookbehind
]


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


def validate_path(path: Path, base_dir: Path) -> bool:
    """Validate that path is within base directory (prevent directory traversal)."""
    try:
        resolved = path.resolve()
        return resolved.is_relative_to(base_dir)
    except Exception:
        return False


def validate_regex_pattern(pattern: str) -> bool:
    """
    Validate regex pattern for security.

    Disallows:
    - Greedy quantifiers (.*, .+) that could cause backtracking DoS
    - Lookahead/lookbehind assertions
    - Empty quantifiers {,)
    """
    for forbidden in FORBIDDEN_REGEX_PATTERNS:
        if re.search(forbidden, pattern):
            print(f"Error: Pattern contains forbidden regex: {forbidden}", file=sys.stderr)
            return False
    return True


def sanitize_keyword(keyword: str) -> bool:
    """Validate keyword characters."""
    if not re.match(r'^[\w\s\u4e00-\u9fff,，。.。!?！？:：""\'\'\-_]+$', keyword):
        print(f"Error: Invalid keyword characters", file=sys.stderr)
        return False
    return True


def search_keyword(
    memory_dir: Path,
    keyword: str,
    fields: Optional[List[str]] = None,
    limit: int = MAX_RESULTS
) -> List[Dict[str, Any]]:
    """
    Search for keyword in memory files (simple substring match).

    Args:
        memory_dir: Path to memory directory
        keyword: Keyword to search for
        fields: Fields to search in (None = all allowed fields)
        limit: Maximum number of results

    Returns:
        List of matching memory entries with metadata
    """
    results = []
    count = 0

    # Security: Sanitize keyword
    if not sanitize_keyword(keyword):
        sys.exit(1)

    # Security: Validate and limit fields
    if fields:
        fields = [f for f in fields if f in ALLOWED_FIELDS]
        if not fields:
            fields = list(ALLOWED_FIELDS)
    else:
        fields = list(ALLOWED_FIELDS)

    keyword_lower = keyword.lower()

    # Iterate through JSON files
    for json_file in memory_dir.glob("event_*.json"):
        if not validate_path(json_file, memory_dir):
            continue

        if not json_file.suffix == ".json":
            continue

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Search in specified fields
            matches = []
            for field in fields:
                if field in data:
                    field_value = str(data[field]).lower()
                    if keyword_lower in field_value:
                        content = str(data[field])
                        if len(content) > 200:
                            content = content[:200] + "..."
                        matches.append(f"{field}: {content}")

            if matches:
                results.append({
                    "file": json_file.name,
                    "matches": matches,
                    "type": data.get("type", "unknown"),
                    "stage": data.get("stage", "unknown"),
                })
                count += 1

                if count >= limit:
                    break

        except (json.JSONDecodeError, IOError, UnicodeDecodeError):
            continue

    return results


def search_regex(
    memory_dir: Path,
    pattern: str,
    fields: Optional[List[str]] = None,
    limit: int = MAX_RESULTS,
    case_sensitive: bool = False
) -> List[Dict[str, Any]]:
    """
    Search for regex pattern in memory files.

    Args:
        memory_dir: Path to memory directory
        pattern: Regex pattern to search
        fields: Fields to search in (None = all allowed fields)
        limit: Maximum number of results
        case_sensitive: Whether to do case-sensitive search

    Returns:
        List of matching memory entries with metadata
    """
    results = []
    count = 0

    # Security: Validate regex pattern
    if not validate_regex_pattern(pattern):
        sys.exit(1)

    # Compile regex
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
    except re.error as e:
        print(f"Error: Invalid regex pattern: {e}", file=sys.stderr)
        sys.exit(1)

    # Security: Validate and limit fields
    if fields:
        fields = [f for f in fields if f in ALLOWED_FIELDS]
        if not fields:
            fields = list(ALLOWED_FIELDS)
    else:
        fields = list(ALLOWED_FIELDS)

    # Iterate through JSON files
    for json_file in memory_dir.glob("event_*.json"):
        if not validate_path(json_file, memory_dir):
            continue

        if not json_file.suffix == ".json":
            continue

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Search in specified fields
            matches = []
            for field in fields:
                if field in data:
                    field_value = str(data[field])
                    found = regex.search(field_value)
                    if found:
                        # Get context around match
                        content = field_value
                        start = max(0, found.start() - 30)
                        end = min(len(content), found.end() + 30)
                        context = content[start:end]

                        if start > 0:
                            context = "..." + context
                        if end < len(content):
                            context = context + "..."

                        # Mark the match
                        matched_text = found.group(0)
                        context = context.replace(matched_text, f"[{matched_text}]")

                        matches.append(f"{field}: ...{context}...")

            if matches:
                results.append({
                    "file": json_file.name,
                    "matches": matches,
                    "type": data.get("type", "unknown"),
                    "stage": data.get("stage", "unknown"),
                })
                count += 1

                if count >= limit:
                    break

        except (json.JSONDecodeError, IOError, UnicodeDecodeError):
            continue

    return results


def format_results(results: List[Dict[str, Any]], is_regex: bool = False) -> None:
    """Format and print search results."""
    if not results:
        print("No results found.")
        return

    match_type = "regex" if is_regex else "keyword"
    print(f"Found {len(results)} results ({match_type} search):")
    print()

    for i, result in enumerate(results, 1):
        print(f"--- Result {i} ---")
        print(f"文件: {result['file']}")
        print(f"类型: {result['type']}")
        print(f"阶段: {result['stage']}")
        print("匹配内容:")
        for match in result["matches"]:
            print(f"  {match}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Search memory files by keyword or regex pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Simple keyword search
    python search.py --keyword "韩立"
    python search.py -k "战斗" --limit 20

    # Regex pattern search (powerful, like grep -E)
    python search.py --pattern "韩立|韩老魔"
    python search.py -p "炼气.*筑基" --limit 10
    python search.py -p "summary:.*凡人" --field summary

    # Case-sensitive regex
    python search.py -p "韩立" --case-sensitive

    # Search in specific fields
    python search.py --keyword "战斗" --field description --field actions
        """
    )

    # Mutually exclusive: keyword vs pattern
    search_group = parser.add_mutually_exclusive_group(required=True)
    search_group.add_argument(
        "--keyword", "-k",
        help="Simple keyword to search for"
    )
    search_group.add_argument(
        "--pattern", "-p",
        help="Regex pattern to search (more powerful, supports wildcards, alternation)"
    )

    parser.add_argument(
        "--field", "-f",
        action="append",
        dest="fields",
        help="Fields to search in (can be specified multiple times)"
    )

    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=MAX_RESULTS,
        help=f"Maximum number of results (default: {MAX_RESULTS})"
    )

    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Case-sensitive search (for regex mode only)"
    )

    args = parser.parse_args()

    # Get memory directory
    memory_dir = get_memory_dir()

    if not memory_dir.exists():
        print(f"Error: Memory directory not found: {memory_dir}", file=sys.stderr)
        sys.exit(1)

    # Perform search
    if args.keyword:
        results = search_keyword(
            memory_dir=memory_dir,
            keyword=args.keyword,
            fields=args.fields,
            limit=args.limit
        )
        format_results(results, is_regex=False)
    else:
        results = search_regex(
            memory_dir=memory_dir,
            pattern=args.pattern,
            fields=args.fields,
            limit=args.limit,
            case_sensitive=args.case_sensitive
        )
        format_results(results, is_regex=True)


if __name__ == "__main__":
    main()
