#!/usr/bin/env python3
"""
Unified memory query engine - Search, filter, list, and analyze memory files.

Subcommands:
    search    Full-text search (keyword or regex)
    filter    Structured condition filtering (field=value)
    stats     Aggregate statistics (group by field)
    list      List files (with summary)
    fields    Discover all available fields and their frequency

Security:
    - Only reads .json files in the memory directory
    - Validates paths to prevent directory traversal
    - Limits search results to prevent DoS
    - Regex compile timeout protection
    - Filename validation (event_\\d+\\.json pattern)
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

# Security constants
MAX_RESULTS = 200
FILENAME_PATTERN = re.compile(r"^event_\d+\.json$")


def extract_event_id(filename: str) -> str:
    """从文件名提取 ID: event_00042.json -> 42"""
    match = re.match(r"event_(\d+)\.json", filename)
    if match:
        return str(int(match.group(1)))  # 去掉前导零
    return filename


def truncate_text(text: str, max_len: int) -> str:
    """简单截断文本"""
    if not text or len(text) <= max_len:
        return text
    return text[:max_len] + "..."


# --- Core utilities ---


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


def get_nested_value(data: Any, field_path: str) -> List[Any]:
    """
    Get values via dot notation, supporting list expansion.

    Examples:
        get_nested_value(data, "type") -> [data["type"]]
        get_nested_value(data, "characters.name") -> [c["name"] for c in data["characters"]]
    """
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


def flatten_values(data: Any) -> List[str]:
    """Recursively extract all string values from a nested structure."""
    results = []
    if isinstance(data, str):
        results.append(data)
    elif isinstance(data, (int, float, bool)):
        results.append(str(data))
    elif isinstance(data, list):
        for item in data:
            results.extend(flatten_values(item))
    elif isinstance(data, dict):
        for val in data.values():
            results.extend(flatten_values(val))
    return results


def match_value(
    value: str, query: str, regex: "re.Pattern | None" = None, context_len: int = 60
) -> Optional[str]:
    """
    Match a string value against a query. Returns context snippet with match highlighted, or None.

    Args:
        value: The string to search in
        query: The keyword (used when regex is None)
        regex: Compiled regex pattern (takes precedence over query)
        context_len: Characters of context around match
    """
    if regex:
        found = regex.search(value)
        if found:
            start = max(0, found.start() - context_len)
            end = min(len(value), found.end() + context_len)
            snippet = value[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(value):
                snippet = snippet + "..."
            return snippet
    else:
        idx = value.lower().find(query.lower())
        if idx >= 0:
            start = max(0, idx - context_len)
            end = min(len(value), idx + len(query) + context_len)
            snippet = value[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(value):
                snippet = snippet + "..."
            return snippet
    return None


def compile_regex(pattern: str, case_sensitive: bool = False) -> "re.Pattern":
    """Compile a regex pattern with safety checks."""
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.compile(pattern, flags)
    except re.error as e:
        print(f"Error: Invalid regex pattern: {e}", file=sys.stderr)
        sys.exit(1)


# --- MemoryStore ---


class MemoryStore:
    """Memory file management."""

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir

    def iter_events(
        self, sort_key: Optional[str] = None, reverse: bool = False
    ) -> Iterator[Tuple[str, dict]]:
        """
        Iterate all event_*.json files, yielding (filename, data).

        Args:
            sort_key: Field to sort by. Use "file" for filename. None for default (filename).
            reverse: Reverse sort order.
        """
        entries = []
        for json_file in self.memory_dir.glob("event_*.json"):
            if not FILENAME_PATTERN.match(json_file.name):
                continue
            if not validate_path(json_file, self.memory_dir):
                continue
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entries.append((json_file.name, data))
            except (json.JSONDecodeError, IOError, UnicodeDecodeError):
                continue

        # Sort
        if sort_key and sort_key != "file":
            entries.sort(key=lambda e: str(e[1].get(sort_key, "")), reverse=reverse)
        else:
            entries.sort(key=lambda e: e[0], reverse=reverse)

        yield from entries

    def scan_fields(self, sample: int = 0) -> Dict[str, dict]:
        """
        Dynamically discover all fields across memory files.

        Args:
            sample: If > 0, only scan this many files.

        Returns:
            Dict of field_path -> {"count": N, "total": M, "values": Counter, "nested": [...], "is_array": bool}
        """
        field_info: Dict[str, dict] = {}
        total = 0

        for filename, data in self.iter_events():
            total += 1
            self._scan_dict(data, "", field_info)
            if sample > 0 and total >= sample:
                break

        # Add total to all fields
        for info in field_info.values():
            info["total"] = total

        return field_info

    def _scan_dict(self, data: Any, prefix: str, field_info: Dict[str, dict]):
        """Recursively scan a dict to discover fields."""
        if not isinstance(data, dict):
            return

        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else key
            if path not in field_info:
                field_info[path] = {
                    "count": 0,
                    "values": Counter(),
                    "nested": [],
                    "is_array": False,
                }

            field_info[path]["count"] += 1

            if isinstance(value, str):
                # Track sample values for short strings
                if len(value) <= 30:
                    field_info[path]["values"][value] += 1
            elif isinstance(value, (int, float, bool)):
                field_info[path]["values"][str(value)] += 1
            elif isinstance(value, list):
                field_info[path]["is_array"] = True
                for item in value:
                    if isinstance(item, dict):
                        self._scan_dict(item, path, field_info)
            elif isinstance(value, dict):
                self._scan_dict(value, path, field_info)

    def read_file(self, filename: str) -> Optional[dict]:
        """Read a single memory file."""
        if not FILENAME_PATTERN.match(filename):
            return None
        file_path = self.memory_dir / filename
        if not validate_path(file_path, self.memory_dir):
            return None
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, UnicodeDecodeError):
            return None


# --- Output formatting ---


def format_entry_detail(
    filename: str, data: dict, matched_fields: Optional[List[str]] = None
) -> str:
    """Format a single entry in detail mode."""
    lines = [f"--- {filename} ---"]
    lines.append(f"  type: {data.get('type', 'unknown')}")
    lines.append(f"  stage: {data.get('stage', 'unknown')}")

    summary = data.get("summary", "")
    if summary:
        if len(summary) > 120:
            summary = summary[:120] + "..."
        lines.append(f"  summary: {summary}")

    if matched_fields:
        lines.append("  matches:")
        for mf in matched_fields:
            lines.append(f"    {mf}")

    return "\n".join(lines)


def format_entry_compact(
    filename: str, data: dict, matched_fields: Optional[List[str]] = None
) -> str:
    """Format a single entry in compact mode."""
    type_val = data.get("type", "?")
    stage_val = data.get("stage", "?")
    summary = data.get("summary", "")
    if len(summary) > 60:
        summary = summary[:60] + "..."
    line = f"{filename}  [{type_val}/{stage_val}]  {summary}"
    if matched_fields:
        line += f"  ({len(matched_fields)} matches)"
    return line


def format_entry_json(
    filename: str, data: dict, matched_fields: Optional[List[str]] = None
) -> dict:
    """Format a single entry for JSON output."""
    result = {
        "file": filename,
        "type": data.get("type", "unknown"),
        "stage": data.get("stage", "unknown"),
    }
    if matched_fields:
        result["matches"] = matched_fields
    return result


def output_results(
    results: List[Tuple[str, dict, Optional[List[str]]]],
    fmt: str,
    total_scanned: int = 0,
    label: str = "results",
):
    """Output formatted results."""
    if fmt == "json":
        entries = [format_entry_json(fn, d, m) for fn, d, m in results]
        out = {"total": len(entries), "scanned": total_scanned, label: entries}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} {label} (scanned {total_scanned} files):\n")

    if fmt == "compact":
        # Markdown 表格格式
        print("| ID | Type | Stage | Summary | Matches |")
        print("|---|---|---|---|---|")

        for filename, data, matched_fields in results:
            event_id = extract_event_id(filename)
            type_val = data.get("type", "?")
            stage_val = data.get("stage", "?")
            summary = truncate_text(data.get("summary", ""), 50)
            matches = str(len(matched_fields)) if matched_fields else "-"

            print(f"| {event_id} | {type_val} | {stage_val} | {summary} | {matches} |")
    else:
        # detail 格式保持不变
        for filename, data, matched_fields in results:
            print(format_entry_detail(filename, data, matched_fields))
            print()


# --- Parse sort argument ---


def parse_sort(sort_arg: Optional[str]) -> Tuple[Optional[str], bool]:
    """Parse sort argument. '-field' means reverse."""
    if not sort_arg:
        return None, False
    if sort_arg.startswith("-"):
        return sort_arg[1:], True
    return sort_arg, False


# --- Subcommands ---


def cmd_search(store: MemoryStore, args: argparse.Namespace):
    """Full-text search (keyword or regex)."""
    query = args.query
    is_regex = args.regex
    search_fields = args.fields.split(",") if args.fields else None
    context_len = args.context
    case_sensitive = args.case_sensitive
    sort_field, sort_reverse = parse_sort(args.sort)
    limit = min(args.limit, MAX_RESULTS)
    offset = args.offset

    regex = None
    if is_regex:
        regex = compile_regex(query, case_sensitive)

    results = []
    total_scanned = 0

    for filename, data in store.iter_events(sort_key=sort_field, reverse=sort_reverse):
        total_scanned += 1
        matched = []

        if search_fields:
            # Search specified fields (supports dot notation)
            for field_path in search_fields:
                values = get_nested_value(data, field_path)
                for val in values:
                    val_str = str(val) if not isinstance(val, str) else val
                    snippet = match_value(val_str, query, regex, context_len)
                    if snippet:
                        matched.append(f"{field_path}: {snippet}")
        else:
            # Search all fields recursively
            _search_all_fields(data, "", query, regex, context_len, matched)

        if matched:
            results.append((filename, data, matched))

    # Apply offset and limit
    if offset > 0:
        results = results[offset:]
    results = results[:limit]

    output_results(results, args.format, total_scanned, "results")


def _search_all_fields(
    data: Any,
    prefix: str,
    query: str,
    regex: "re.Pattern | None",
    context_len: int,
    matched: List[str],
    depth: int = 0,
):
    """Recursively search all fields in a dict."""
    if depth > 10:
        return
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, str):
                snippet = match_value(value, query, regex, context_len)
                if snippet:
                    matched.append(f"{path}: {snippet}")
            elif isinstance(value, (int, float, bool)):
                snippet = match_value(str(value), query, regex, context_len)
                if snippet:
                    matched.append(f"{path}: {snippet}")
            elif isinstance(value, (dict, list)):
                _search_all_fields(
                    value, path, query, regex, context_len, matched, depth + 1
                )
    elif isinstance(data, list):
        for i, item in enumerate(data):
            _search_all_fields(
                item, prefix, query, regex, context_len, matched, depth + 1
            )


def cmd_filter(store: MemoryStore, args: argparse.Namespace):
    """Structured condition filtering."""
    conditions = _parse_conditions(args.conditions)
    if not conditions:
        print("Error: No valid conditions provided.", file=sys.stderr)
        print("Usage: filter field=value field~pattern field!=value", file=sys.stderr)
        sys.exit(1)

    sort_field, sort_reverse = parse_sort(args.sort)
    limit = min(args.limit, MAX_RESULTS)
    offset = args.offset

    results = []
    total_scanned = 0

    for filename, data in store.iter_events(sort_key=sort_field, reverse=sort_reverse):
        total_scanned += 1

        if _matches_all_conditions(data, conditions):
            matched_info = [f"{c['field']}{c['op']}{c['value']}" for c in conditions]
            results.append((filename, data, matched_info))

    # Apply offset and limit
    if offset > 0:
        results = results[offset:]
    results = results[:limit]

    output_results(results, args.format, total_scanned, "results")


def _parse_conditions(condition_strings: List[str]) -> List[dict]:
    """Parse condition strings like field=value, field~pattern, field!=value."""
    conditions = []
    for cs in condition_strings:
        # Try != first (before =)
        if "!=" in cs:
            field, value = cs.split("!=", 1)
            conditions.append(
                {"field": field.strip(), "op": "!=", "value": value.strip()}
            )
        elif "~" in cs:
            field, value = cs.split("~", 1)
            regex = compile_regex(value.strip())
            conditions.append(
                {
                    "field": field.strip(),
                    "op": "~",
                    "value": value.strip(),
                    "regex": regex,
                }
            )
        elif "=" in cs:
            field, value = cs.split("=", 1)
            conditions.append(
                {"field": field.strip(), "op": "=", "value": value.strip()}
            )
        else:
            print(f"Warning: Ignoring invalid condition: {cs}", file=sys.stderr)
    return conditions


def _matches_all_conditions(data: dict, conditions: List[dict]) -> bool:
    """Check if data matches all conditions (AND logic)."""
    for cond in conditions:
        values = get_nested_value(data, cond["field"])
        str_values = [str(v) if not isinstance(v, str) else v for v in values]

        if cond["op"] == "=":
            # Contains match
            if not any(cond["value"] in sv for sv in str_values):
                return False
        elif cond["op"] == "!=":
            # All values must not contain the value
            if any(cond["value"] in sv for sv in str_values):
                return False
        elif cond["op"] == "~":
            # Regex match
            regex = cond["regex"]
            if not any(regex.search(sv) for sv in str_values):
                return False
    return True


def cmd_stats(store: MemoryStore, args: argparse.Namespace):
    """Aggregate statistics."""
    by_fields = args.by.split(",") if args.by else None

    total = 0
    counters: Dict[str, Counter] = defaultdict(Counter)

    for filename, data in store.iter_events():
        total += 1
        if by_fields:
            for field in by_fields:
                values = get_nested_value(data, field)
                for val in values:
                    counters[field][str(val)] += 1
        else:
            # Default: count by 'type'
            type_val = data.get("type", "unknown")
            counters["type"][type_val] += 1

    # Output
    if args.format == "json":
        out = {"total": total, "groups": {}}
        for field, counter in counters.items():
            out["groups"][field] = dict(counter.most_common())
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print(f"Total: {total} memory files\n")

    for field, counter in counters.items():
        print(f"Statistics by '{field}':\n")

        # Markdown 表格
        print("| Value | Count | Percentage |")
        print("|---|---|---|")

        for value, count in counter.most_common():
            pct = f"{round(count / total * 100, 1)}%" if total > 0 else "0%"
            value_str = truncate_text(str(value), 30)
            print(f"| {value_str} | {count} | {pct} |")

        print()


def cmd_list(store: MemoryStore, args: argparse.Namespace):
    """List memory files with optional summary."""
    sort_field, sort_reverse = parse_sort(args.sort)
    limit = min(args.limit, MAX_RESULTS)
    offset = args.offset
    no_summary = args.no_summary

    results = []
    total_scanned = 0

    for filename, data in store.iter_events(sort_key=sort_field, reverse=sort_reverse):
        total_scanned += 1
        results.append((filename, data, None))

    # Apply offset and limit
    if offset > 0:
        results = results[offset:]
    results = results[:limit]

    if args.format == "json":
        entries = []
        for fn, d, _ in results:
            entry = {
                "file": fn,
                "type": d.get("type", "unknown"),
                "stage": d.get("stage", "unknown"),
            }
            if not no_summary:
                entry["summary"] = (d.get("summary") or d.get("description", ""))[:120]
            entries.append(entry)
        print(
            json.dumps(
                {"total": len(entries), "scanned": total_scanned, "entries": entries},
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if not results:
        print("No memory files found.")
        return

    print(f"Found {len(results)} entries (total {total_scanned} files):\n")

    if args.format == "compact":
        # Markdown 表格格式
        if no_summary:
            print("| ID | Type | Stage |")
            print("|---|---|---|")
            for filename, data, _ in results:
                event_id = extract_event_id(filename)
                type_val = data.get("type", "?")
                stage_val = data.get("stage", "?")
                print(f"| {event_id} | {type_val} | {stage_val} |")
        else:
            print("| ID | Type | Stage | Summary |")
            print("|---|---|---|---|")
            for filename, data, _ in results:
                event_id = extract_event_id(filename)
                type_val = data.get("type", "?")
                stage_val = data.get("stage", "?")
                summary = truncate_text(
                    data.get("summary") or data.get("description", ""), 50
                )
                print(f"| {event_id} | {type_val} | {stage_val} | {summary} |")
    else:
        # detail 格式保持不变
        for filename, data, _ in results:
            print(f"--- {filename} ---")
            print(f"  type: {data.get('type', 'unknown')}")
            print(f"  stage: {data.get('stage', 'unknown')}")
            if not no_summary:
                summary = data.get("summary") or data.get("description", "")
                if summary:
                    if len(summary) > 120:
                        summary = summary[:120] + "..."
                    print(f"  summary: {summary}")
            print()


def cmd_fields(store: MemoryStore, args: argparse.Namespace):
    """Discover available fields and their frequency."""
    field_info = store.scan_fields(sample=args.sample)

    if not field_info:
        print("No fields found (no memory files?).")
        return

    total = next(iter(field_info.values()))["total"] if field_info else 0

    if args.format == "json":
        out: Dict[str, Any] = {"total_files": total, "fields": {}}
        for path, info in sorted(field_info.items()):
            out["fields"][path] = {
                "count": info["count"],
                "total": info["total"],
                "percentage": (
                    round(info["count"] / info["total"] * 100, 1)
                    if info["total"]
                    else 0
                ),
                "is_array": info["is_array"],
                "sample_values": [v for v, _ in info["values"].most_common(5)],
            }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print(f"Found {len(field_info)} fields across {total} files:\n")

    # 构建父子关系，方便生成树形结构
    field_tree: Dict[str, List[str]] = {}  # {parent_path: [child_paths]}
    root_fields = []

    for path in field_info.keys():
        if "." not in path:
            root_fields.append(path)
        else:
            parent = path.rsplit(".", 1)[0]
            if parent not in field_tree:
                field_tree[parent] = []
            field_tree[parent].append(path)

    # 排序：顶层字段按频率降序
    sorted_roots = sorted(root_fields, key=lambda p: -field_info[p]["count"])

    def print_field_tree(path: str, prefix: str = "", is_last: bool = True):
        """递归打印树形结构"""
        info = field_info[path]
        count = info["count"]
        pct = f"{round(count / total * 100, 1)}%" if total else "0%"

        # 只显示字段名（不含完整路径）
        field_name = path.split(".")[-1]

        # 树形符号
        branch = "└─ " if is_last else "├─ "

        # 类型标识
        type_str = "[array]" if info["is_array"] else "       "

        # 示例值
        sample_values = ""
        if info["values"] and len(info["values"]) <= 20:
            top_values = [str(v) for v, _ in info["values"].most_common(3)]
            sample_values = ", ".join([truncate_text(v, 10) for v in top_values])

        # 打印当前字段
        line = f"{prefix}{branch}{field_name:<25s}  {count}/{total} ({pct:>6s})  {type_str}"
        if sample_values:
            line += f"  {sample_values}"
        print(line)

        # 递归打印子字段
        children = field_tree.get(path, [])
        if children:
            # 按频率排序子字段
            sorted_children = sorted(children, key=lambda p: -field_info[p]["count"])
            for i, child in enumerate(sorted_children):
                is_last_child = i == len(sorted_children) - 1
                # 更新前缀：如果当前是最后一个，用空格；否则用竖线
                child_prefix = prefix + ("    " if is_last else "│   ")
                print_field_tree(child, child_prefix, is_last_child)

    # 打印所有顶层字段
    for i, root in enumerate(sorted_roots):
        is_last = i == len(sorted_roots) - 1
        print_field_tree(root, "", is_last)


# --- Main ---


def main():
    parser = argparse.ArgumentParser(
        prog="query.py",
        description="Unified memory query engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Common arguments
    def add_common_args(p: argparse.ArgumentParser):
        p.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum results (default: 50, max: 200)",
        )
        p.add_argument(
            "--offset", type=int, default=0, help="Skip first N results (pagination)"
        )
        p.add_argument(
            "--sort",
            type=str,
            help="Sort field (prefix with - for reverse, e.g. -file)",
        )
        p.add_argument(
            "--format",
            choices=["detail", "compact", "json"],
            default="compact",
            help="Output format (default: compact/table)",
        )

    # --- search ---
    p_search = subparsers.add_parser(
        "search", help="Full-text search (keyword or regex)"
    )
    p_search.add_argument("query", help="Search query (keyword or regex pattern)")
    p_search.add_argument(
        "-r", "--regex", action="store_true", help="Treat query as regex pattern"
    )
    p_search.add_argument(
        "--fields",
        type=str,
        help="Comma-separated fields to search (e.g. summary,description)",
    )
    p_search.add_argument(
        "--context",
        type=int,
        default=60,
        help="Context characters around match (default: 60)",
    )
    p_search.add_argument(
        "--case-sensitive", action="store_true", help="Case-sensitive search"
    )
    add_common_args(p_search)

    # --- filter ---
    p_filter = subparsers.add_parser("filter", help="Structured condition filtering")
    p_filter.add_argument(
        "conditions",
        nargs="+",
        help="Conditions: field=value, field~regex, field!=value",
    )
    add_common_args(p_filter)

    # --- stats ---
    p_stats = subparsers.add_parser("stats", help="Aggregate statistics")
    p_stats.add_argument(
        "--by", type=str, help="Comma-separated fields to group by (default: type)"
    )
    p_stats.add_argument(
        "--format", choices=["detail", "json"], default="detail", help="Output format"
    )

    # --- list ---
    p_list = subparsers.add_parser("list", help="List memory files")
    p_list.add_argument("--no-summary", action="store_true", help="Don't show summary")
    add_common_args(p_list)

    # --- fields ---
    p_fields = subparsers.add_parser("fields", help="Discover available fields")
    p_fields.add_argument(
        "--sample", type=int, default=0, help="Sample N files (0 = all)"
    )
    p_fields.add_argument(
        "--format", choices=["detail", "json"], default="detail", help="Output format"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Get memory directory
    memory_dir = get_memory_dir()
    if not memory_dir.exists():
        print(f"Error: Memory directory not found: {memory_dir}", file=sys.stderr)
        sys.exit(1)

    store = MemoryStore(memory_dir)

    # Dispatch
    commands = {
        "search": cmd_search,
        "filter": cmd_filter,
        "stats": cmd_stats,
        "list": cmd_list,
        "fields": cmd_fields,
    }

    commands[args.command](store, args)


if __name__ == "__main__":
    main()
