from pathlib import Path
from typing import Any
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
import time

from modules.core.timestamp import build_timestamp
from modules.config.config import load_pattern_search_rule
from modules.io.file_utils import (get_files_in_folder, get_file_info)
from modules.io.exporters import (write_csv, convert_csv_to_excel)
from modules.core.parser import (
    yield_event_block,
    extract_matches_from_event_block,
    is_keyword_event,
    yield_event_block_with_progress
)
from modules.utils.thread_executor import run_with_threading

# ========== Rows and headers Generator ==========

def collect_rows_and_headers(
    files: list,
    separator_regex,
    compiled,
    keyword: str,
    show_progress: bool
):
    headers = []
    rows = []
    
    files_info: list[dict[str, Any]] = run_with_threading(get_file_info, files)

    for file in files_info:
        date_created: str = file["Created"].split("-")[0].strip()
        filepath: Path = file["Filepath"]
        total_lines: int = file["Lines"]
        
        # Work
        rprint(f"[blue]Processing: {filepath.name}[/blue]")
        
        # Choose generator once
        block_iter = (
            yield_event_block_with_progress(filepath, separator_regex, total_lines)
            if show_progress
            else yield_event_block(filepath, separator_regex)
        )
        
        for block in block_iter:
            if keyword and not is_keyword_event(keyword, block):
                continue

            row = extract_matches_from_event_block(block, compiled)
            
            if not row:
                continue

            # Timestamp header handling
            if "time" in row:
                row["timestamp"] = build_timestamp(row["time"], filepath, date_created)
                del row["time"]
            else:
                row["timestamp"] = date_created

            # Filter empty rows (ignore timestamp)
            if not is_empty_row(row, "timestamp"):
                continue
            
            # collect headers (ordered, no duplicates)
            for key in row:
                if key not in headers:
                    headers.append(key)

            rows.append(row)

    return rows, headers


def is_empty_row(row: dict, ignore_key: str) -> bool:
    # Filter empty rows (ignore timestamp)
    return any(
        v not in (None, "")
        for k, v in row.items()
        if k != ignore_key)


def display_finished_msg(output_csv: Path, count: int, total_time: str, excel_msg: str, rows_found: bool = True):
    """Display completion message with consistent styling."""
    console = Console()
    if rows_found:
        content = f"[green]✓ Task has finished in {total_time} seconds\n\nWrote {count} rows to {output_csv}\n{excel_msg}[/green]"
        title = "[bold green]Success[/bold green]"
    else:
        content = f"[yellow]No matches were found, nothing to write.\n\nProcess finished in {total_time} seconds.[/yellow]"
        title = "[bold yellow]Warning[/bold yellow]"
    
    panel = Panel(content, title=title, expand=False)
    console.print(panel)
    

# ========== Pipeline ==========

def run_pipeline(
        patterns_config: Path,
        pattern_key: str,
        files_directory: Path,
        file_pattern: str,
        output_csv: Path,
        event_keyword: str = "",
        show_progress: bool = False
):
    
    start = time.time() # Process start time

    compiled, separator_regex = load_pattern_search_rule(patterns_config, pattern_key)

    files = get_files_in_folder(files_directory, file_pattern)

    if not files:
        raise ValueError(
            f"No files found in {files_directory}, using pattern {file_pattern}")

    # Collect rows + headers in one pass
    rows, headers = collect_rows_and_headers(
        files, separator_regex, compiled, event_keyword, show_progress
    )

    # Normalize headers
    headers = ["timestamp"] + \
        [h for h in headers if h not in ("time", "timestamp")]

    # Write CSV if data was found
    if rows:
        count = write_csv(output_csv, headers, rows)
        excel_msg = convert_csv_to_excel(output_csv, output_csv.with_suffix(".xlsx")) # Convert to excel
        end = time.time() # Process end time
        total_time = f"{end - start:.2f}" # Total time taken
        display_finished_msg(output_csv, count, total_time, excel_msg, rows_found=True)
    else:
        display_finished_msg(output_csv, 0, total_time, "", rows_found=False)
