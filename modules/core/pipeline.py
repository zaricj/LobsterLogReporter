from pathlib import Path
from rich.console import Console
from rich.panel import Panel

import time

from modules.config.config import load_pattern_search_rule
from modules.io.file_utils import get_files_in_folder
from modules.io.exporters import (write_csv, convert_csv_to_excel)
from modules.core.utils import collect_rows_and_headers

def display_finished_msg(output_csv: Path, count: int, total_time: str, excel_msg: str, rows_found: bool):
    """Display completion message with consistent styling."""
    console = Console()
    if rows_found:
        content = f"[green]✓ Task has finished in {total_time} seconds\n\nWrote {count} rows to: {output_csv}\n{excel_msg}[/green]"
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
    Console().rule("Starting pipeline task")
    
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
