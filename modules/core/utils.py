import json
import re
from pathlib import Path
from rich import print as rprint

from modules.core.parser import (
    yield_event_block,
    extract_matches_from_event_block,
    yield_event_block_with_progress
)
from modules.core.thread_executor import run_with_threading
from modules.core.timestamp import (build_timestamp, extract_date_from_filename)
from modules.io.file_utils import get_file_info

# ========== Load & Compile Patterns ==========

def load_patterns_json(filepath: Path) -> dict[str, str]:
    with filepath.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_pattern_keys(filepath: Path) -> list[str]:
    patterns = load_patterns_json(filepath)
    return list(patterns.keys())


def compile_regex(pattern: str, flags=0):
    return re.compile(pattern, flags)


def compile_regex_patterns(category_config: dict):
    """Compile base separator + patterns for one category"""
    compiled = {}
    compiled["base"] = {name: re.compile(
        p) for name, p in category_config.get("base", {}).items()}
    compiled["patterns"] = {name: re.compile(p, re.MULTILINE | re.DOTALL)
                            for name, p in category_config.get("patterns", {}).items()}
    return compiled

# ========== Rows and headers Generator ==========

def collect_rows_and_headers(
    files: list, separator_regex, compiled, keyword: str, show_progress: bool
):
    headers = []
    headers_seen = set() # Optimization: O(1) lookup
    rows = []

    files_info = run_with_threading(get_file_info, files)
    
    # Pre-compile keyword regex to avoid .lower() on every block
    keyword_re = re.compile(re.escape(keyword), re.IGNORECASE) if keyword else None

    for file in files_info:
        if not file: continue
        
        filepath: Path = file["Filepath"]
        # CACHE these values once per file
        date_created = file["Created"].split("-")[0].strip()
        filename_date = extract_date_from_filename(filepath) or date_created
        
        rprint(f"Processing: [bold blue]{filepath.name}[/bold blue]")

        block_iter = (
            yield_event_block_with_progress(filepath, separator_regex, file["Lines"])
            if show_progress else yield_event_block(filepath, separator_regex)
        )

        for block in block_iter:
            if keyword_re and not keyword_re.search(block):
                continue

            row = extract_matches_from_event_block(block, compiled)
            if not row: 
                continue

            # Optimized timestamping
            parsed_time = row.get("time")
            row["timestamp"] = build_timestamp(parsed_time, filename_date) if parsed_time else filename_date
            row.pop("time", None)

            if not is_empty_row(row, "timestamp"):
                continue

            # Optimized header collection
            for key in row:
                if key not in headers_seen:
                    headers.append(key)
                    headers_seen.add(key)
            rows.append(row)
    rprint(f"[bold]>>> Processed and searched [green]{len(files)}[/green] files...[/bold]")
    return rows, headers


def is_empty_row(row: dict, ignore_key: str) -> bool:
    # Filter empty rows (ignore timestamp)
    return any(
        v not in (None, "")
        for k, v in row.items()
        if k != ignore_key)
