from pathlib import Path
import time
import itertools
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from modules.io.converters import str_to_path
from modules.io.file_utils import get_files_in_folder
from modules.io.exporters import write_csv, convert_csv_to_excel
from modules.config.config import load_pattern_search_rule
from modules.core.utils import collect_rows, collect_headers

CONSOLE = Console()


def display_start_msg(
    patterns_config: str | Path,
    pattern_key: str,
    files_directory: str | Path,
    file_pattern: str,
    event_keyword: str,
):
    if not event_keyword:
        content = f"[bold blue]Pattern config: [/bold blue]{patterns_config}\n[bold blue]Pattern key: [/bold blue]{pattern_key}\n[bold blue]Searching dir: [/bold blue]{files_directory}\n[bold blue]File pattern: [/bold blue]{file_pattern}"
    else:
        content = f"[bold blue]Pattern config: [/bold blue]{patterns_config}\n[bold blue]Pattern key: [/bold blue]{pattern_key}\n[bold blue]Searching dir: [/bold blue]{files_directory}\n[bold blue]File pattern: [/bold blue]{file_pattern}\n[bold blue]Event keyword: [/bold blue]{event_keyword}"
    panel = Panel(
        content, title="[bold blue]Starting pipeline task[/bold blue]", expand=False
    )
    CONSOLE.print(panel)


def display_finished_msg(output_csv: str, excel_filename: str, total_time: str, rows_found: bool):
    """Display completion message with consistent styling."""

    if rows_found:
        content = f"[green]CSV saved: {output_csv}\nExcel saved: {excel_filename}\n>>> ✓ Task has finished in {total_time} seconds. <<<[/green]"
        title = "[bold green]Success[/bold green]"
    else:
        content = f"[yellow]No matches were found, nothing to write.\n✓ Task has finished in {total_time} seconds.[/yellow]"
        title = "[bold yellow]Warning[/bold yellow]"

    panel = Panel(content, title=title, expand=False)
    CONSOLE.print(panel)


# ========== Pipeline ==========


def run_pipeline(
    patterns_config: str | Path,
    pattern_key: str,
    files_directory: str | Path,
    file_pattern: str,
    output_csv: str | Path,
    event_keyword: str = "",
    show_progress: bool = False,
):

    # Str to Path conversion if needed
    for i, obj in enumerate([patterns_config, files_directory, output_csv]):
        match i:
            case 0:
                patterns_config = str_to_path(obj)
            case 1:
                files_directory = str_to_path(obj)
            case 2:
                output_csv = str_to_path(obj)
                
    display_start_msg(patterns_config, pattern_key, files_directory, file_pattern, event_keyword)

    start = time.time()  # Process start time

    compiled, separator_regex = load_pattern_search_rule(patterns_config, pattern_key)

    files = get_files_in_folder(files_directory, file_pattern)

    if not files:
        raise ValueError(
            f"No files found in {files_directory}, using pattern {file_pattern}"
        )

    # Collect rows as generator object
    row_generator = collect_rows(files, separator_regex, compiled, event_keyword, show_progress)
    first_row = next(row_generator, None)

    # Check if we actually yielded any data
    if first_row is not None: 
        # Collect headers from the extracted first row
        headers = ["timestamp"] + [h for h in first_row.keys() if h not in ("time", "timestamp")]
        
        # 3. Stitch the first row back together with the remaining generator
        full_generator = itertools.chain([first_row], row_generator)
        
        
        # Pass the stitched generator to your writer
        rprint("[bold]>>> Writing results to csv file...[/bold]")
        count = write_csv(output_csv, headers, full_generator)
        excel_filename = output_csv.with_suffix(".xlsx")
        
        rprint(f"[bold green]✓ Writing to csv has finished, wrote [yellow]{count}[/yellow] rows...[/bold green]")
        convert_csv_to_excel(output_csv, excel_filename)  # Convert to excel
        rprint("[bold green]✓ CSV converted to excel format.[/bold green]")
        
        end = time.time()
        total_time = f"{end - start:.2f}"
        display_finished_msg(str(output_csv), str(excel_filename), total_time, True)
    else:
        # No rows found
        display_finished_msg("", "", "0", False) # Adjusted to match your params

