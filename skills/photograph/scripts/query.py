#!/usr/bin/env python3
"""
Photo asset query engine - Search, filter, and list photo assets.

Subcommands:
    search    Full-text search (description + tags)
    filter    Structured condition filtering (field=value)
    list      List assets (with description)
    fields    Discover all category values

Security:
    - Only reads .json files in the assets directory
    - Validates paths to prevent directory traversal
    - Limits search results to prevent DoS
    - Filename validation (asset_*.json pattern)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

# Security constants
MAX_RESULTS = 200
FILENAME_PATTERN = re.compile(r"^asset_.+\.json$")


def truncate_text(text: str, max_len: int) -> str:
    if not text or len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def normalize_value(value: str, max_len: int = 0) -> str:
    if not value or value in ["未明确", "-"]:
        return "?"
    if max_len > 0 and len(value) > max_len:
        return value[:max_len] + "..."
    return value


# --- Core utilities ---


def get_assets_dir() -> Path:
    assets_dir = os.environ.get("PHOTO_ASSETS_DIR")
    if not assets_dir:
        print("Error: PHOTO_ASSETS_DIR not set", file=sys.stderr)
        sys.exit(1)
    return Path(assets_dir).resolve()


def validate_path(path: Path, base_dir: Path) -> bool:
    try:
        resolved = path.resolve()
        return resolved.is_relative_to(base_dir)
    except Exception:
        return False


def get_nested_value(data: Any, field_path: str) -> List[Any]:
    parts = field_path.split(".")
    current = [data]
    for part in parts:
        next_values = []
        for item in current:
            if isinstance(item, dict) and part in item:
                val = item[part]
                if isinstance(val, list):
                    next_values.extend(val)
                else:
                    next_values.append(val)
            elif isinstance(item, list):
                for sub in item:
                    if isinstance(sub, dict) and part in sub:
                        val = sub[part]
                        if isinstance(val, list):
                            next_values.extend(val)
                        else:
                            next_values.append(val)
        current = next_values
    return current


def compile_regex(pattern: str, case_sensitive: bool = False) -> "re.Pattern":
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.compile(pattern, flags)
    except re.error as e:
        print(f"Error: Invalid regex pattern: {e}", file=sys.stderr)
        sys.exit(1)


# --- AssetStore ---


class AssetStore:
    def __init__(self, assets_dir: Path):
        self.assets_dir = assets_dir

    def iter_assets(self, sort_key: Optional[str] = None, reverse: bool = False) -> Iterator[Tuple[str, dict]]:
        entries = []
        for json_file in self.assets_dir.glob("asset_*.json"):
            if not FILENAME_PATTERN.match(json_file.name):
                continue
            if not validate_path(json_file, self.assets_dir):
                continue
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entries.append((json_file.name, data))
            except (json.JSONDecodeError, IOError, UnicodeDecodeError):
                continue

        if sort_key and sort_key != "file":
            entries.sort(key=lambda e: str(e[1].get(sort_key, "")), reverse=reverse)
        else:
            entries.sort(key=lambda e: e[0], reverse=reverse)

        yield from entries

    def scan_categories(self) -> Dict[str, int]:
        from collections import Counter
        counter: Counter = Counter()
        for _, data in self.iter_assets():
            cat = data.get("category", "")
            if cat:
                counter[cat] += 1
        return dict(counter.most_common())


# --- Output formatting ---


def format_compact(results: List[Tuple[str, dict, Optional[List[str]]]], total_scanned: int):
    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} results (scanned {total_scanned} files):\n")

    print("| ID | CATEGORY | TAGS | PATH | DESCRIPTION |")
    print("|---|---|---|---|---|")

    for filename, data, _ in results:
        asset_id = data.get("id", filename)
        category = normalize_value(data.get("category", ""))
        tags = data.get("tags", [])
        tags_str = normalize_value(",".join(tags) if isinstance(tags, list) else str(tags))
        path = normalize_value(data.get("path", ""))
        desc = normalize_value(data.get("description", ""), 60)
        print(f"| {asset_id} | {category} | {tags_str} | {path} | {desc} |")


def format_json_output(results: List[Tuple[str, dict, Optional[List[str]]]], total_scanned: int):
    entries = []
    for fn, d, matches in results:
        entry = {
            "file": fn,
            "id": d.get("id", ""),
            "category": d.get("category", ""),
            "path": d.get("path", ""),
            "tags": d.get("tags", []),
            "description": d.get("description", ""),
        }
        if matches:
            entry["matches"] = matches
        entries.append(entry)
    print(json.dumps({"total": len(entries), "scanned": total_scanned, "results": entries}, ensure_ascii=False, indent=2))


# --- Parse sort argument ---


def parse_sort(sort_arg: Optional[str]) -> Tuple[Optional[str], bool]:
    if not sort_arg:
        return None, False
    if sort_arg.startswith("-"):
        return sort_arg[1:], True
    return sort_arg, False


# --- Subcommands ---


def cmd_search(store: AssetStore, args: argparse.Namespace):
    query = args.query
    limit = min(args.limit, MAX_RESULTS)

    results = []
    total_scanned = 0

    for filename, data in store.iter_assets():
        total_scanned += 1

        # Search in description and tags
        search_texts = [data.get("description", "")]
        tags = data.get("tags", [])
        if isinstance(tags, list):
            search_texts.extend(tags)
        else:
            search_texts.append(str(tags))

        matched = []
        q_lower = query.lower()
        for text in search_texts:
            if q_lower in text.lower():
                matched.append(text)
                break

        if matched:
            results.append((filename, data, matched))

    results = results[:limit]

    if args.format == "json":
        format_json_output(results, total_scanned)
    else:
        format_compact(results, total_scanned)


def cmd_filter(store: AssetStore, args: argparse.Namespace):
    conditions = _parse_conditions(args.conditions)
    if not conditions:
        print("Error: No valid conditions provided.", file=sys.stderr)
        print("Usage: filter field=value field~pattern field!=value", file=sys.stderr)
        sys.exit(1)

    sort_field, sort_reverse = parse_sort(args.sort)
    limit = min(args.limit, MAX_RESULTS)

    results = []
    total_scanned = 0

    for filename, data in store.iter_assets(sort_key=sort_field, reverse=sort_reverse):
        total_scanned += 1
        if _matches_all_conditions(data, conditions):
            matched_info = [f"{c['field']}{c['op']}{c['value']}" for c in conditions]
            results.append((filename, data, matched_info))

    results = results[:limit]

    if args.format == "json":
        format_json_output(results, total_scanned)
    else:
        format_compact(results, total_scanned)


def _parse_conditions(condition_strings: List[str]) -> List[dict]:
    conditions = []
    for cs in condition_strings:
        if "!=" in cs:
            field, value = cs.split("!=", 1)
            conditions.append({"field": field.strip(), "op": "!=", "value": value.strip()})
        elif "~" in cs:
            field, value = cs.split("~", 1)
            regex = compile_regex(value.strip())
            conditions.append({"field": field.strip(), "op": "~", "value": value.strip(), "regex": regex})
        elif "=" in cs:
            field, value = cs.split("=", 1)
            conditions.append({"field": field.strip(), "op": "=", "value": value.strip()})
        else:
            print(f"Warning: Ignoring invalid condition: {cs}", file=sys.stderr)
    return conditions


def _matches_all_conditions(data: dict, conditions: List[dict]) -> bool:
    for cond in conditions:
        values = get_nested_value(data, cond["field"])
        str_values = [str(v) if not isinstance(v, str) else v for v in values]

        if cond["op"] == "=":
            if not any(cond["value"] in sv for sv in str_values):
                return False
        elif cond["op"] == "!=":
            if any(cond["value"] in sv for sv in str_values):
                return False
        elif cond["op"] == "~":
            regex = cond["regex"]
            if not any(regex.search(sv) for sv in str_values):
                return False
    return True


def cmd_list(store: AssetStore, args: argparse.Namespace):
    sort_field, sort_reverse = parse_sort(args.sort)
    limit = min(args.limit, MAX_RESULTS)

    results = []
    total_scanned = 0

    for filename, data in store.iter_assets(sort_key=sort_field, reverse=sort_reverse):
        total_scanned += 1
        results.append((filename, data, None))

    results = results[:limit]

    if args.format == "json":
        format_json_output(results, total_scanned)
    else:
        format_compact(results, total_scanned)


def cmd_fields(store: AssetStore, args: argparse.Namespace):
    categories = store.scan_categories()
    total = sum(categories.values())

    if args.format == "json":
        print(json.dumps({"total_files": total, "categories": categories}, ensure_ascii=False, indent=2))
        return

    if not categories:
        print("No assets found.")
        return

    print(f"Total {total} assets, categories:\n")
    print(f"{'CATEGORY':<15}  COUNT")
    print("-" * 25)
    for cat, count in categories.items():
        pct = f"{round(count / total * 100, 1)}%" if total > 0 else "0%"
        print(f"{cat:<15}  {count} ({pct})")


# --- Main ---


def main():
    parser = argparse.ArgumentParser(
        prog="query.py",
        description="Photo asset query engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    def add_common_args(p: argparse.ArgumentParser):
        p.add_argument("--limit", type=int, default=50, help="Maximum results (default: 50, max: 200)")
        p.add_argument("--sort", type=str, help="Sort field (prefix with - for reverse)")
        p.add_argument(
            "--format",
            choices=["compact", "json"],
            default="compact",
            help="Output format (default: compact)",
        )

    # --- search ---
    p_search = subparsers.add_parser("search", help="Full-text search (description + tags)")
    p_search.add_argument("query", help="Search keyword")
    add_common_args(p_search)

    # --- filter ---
    p_filter = subparsers.add_parser("filter", help="Structured condition filtering")
    p_filter.add_argument("conditions", nargs="+", help="Conditions: field=value, field~regex, field!=value")
    add_common_args(p_filter)

    # --- list ---
    p_list = subparsers.add_parser("list", help="List all assets")
    add_common_args(p_list)

    # --- fields ---
    p_fields = subparsers.add_parser("fields", help="Discover category values")
    p_fields.add_argument("--format", choices=["compact", "json"], default="compact", help="Output format")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    assets_dir = get_assets_dir()
    if not assets_dir.exists():
        print(f"Error: PHOTO_ASSETS_DIR not found: {assets_dir}", file=sys.stderr)
        sys.exit(1)

    store = AssetStore(assets_dir)

    commands = {
        "search": cmd_search,
        "filter": cmd_filter,
        "list": cmd_list,
        "fields": cmd_fields,
    }

    commands[args.command](store, args)


if __name__ == "__main__":
    main()
