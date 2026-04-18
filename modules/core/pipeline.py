from pathlib import Path
from typing import Any
import time

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
        date_modified = file["Modified"].split("-")[0].strip()
        filepath = file["Filepath"]
        total_lines = file["Lines"]
        
        # Work
        print(f"Processing: {filepath}")
        
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

            # Timestamp handling
            if "time" in row:
                row["timestamp"] = f"{date_modified} {row["time"].strip()}"
                del row["time"]
            else:
                row["timestamp"] = date_modified

            # Filter empty rows (ignore timestamp)
            if not any(
                v not in (None, "")
                for k, v in row.items()
                if k != "timestamp"
            ):
                continue

            # collect headers (ordered, no duplicates)
            for key in row:
                if key not in headers:
                    headers.append(key)

            rows.append(row)

    return rows, headers


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
        print(f"\nDone. {count} rows written to {output_csv}")
        # Convert to excel
        output_excel = output_csv.with_suffix(".xlsx")
        convert_csv_to_excel(output_csv, output_excel)
    else:
        print("No matches found, nothing to write.")
        
    end = time.time() # Process end time
    total_time = f"{end - start:.2f}" # Total time taken
    print(f"\nProcess finished in {total_time} seconds.")