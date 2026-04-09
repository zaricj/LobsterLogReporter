import re
from pathlib import Path

from utility.config import load_config
from utility.file_utils import get_files_in_folder
from utility.exporters import write_csv, convert_csv_to_excel
from utility.parser import (
    yield_event_block,
    extract_matches_from_event_block,
    is_keyword_event,
    extract_log_date,
    yield_event_block_with_progress
)

# ========== Rows and headers Generator ==========

def collect_rows_and_headers(
    files: list,
    header_regex,
    compiled,
    keyword: str,
    show_progress: bool
):
    headers = []
    rows = []

    for file in files:
        log_date = extract_log_date(file)
        print(f"Processing: {file}")

        # Choose generator once
        block_iter = (
            yield_event_block_with_progress(file, header_regex)
            if show_progress
            else yield_event_block(file, header_regex)
        )

        for block in block_iter:
            if keyword and not is_keyword_event(keyword, block):
                continue

            row = extract_matches_from_event_block(block, compiled)
            if not row:
                continue

            # timestamp handling
            if "time" in row:
                row["timestamp"] = f"{log_date} {row['time']}".strip()
                del row["time"]
            else:
                row["timestamp"] = log_date

            # filter empty rows (ignore timestamp)
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
        show_progress: bool = False):

    compiled, header_regex = load_config(patterns_config, pattern_key)

    files = get_files_in_folder(files_directory, file_pattern)

    if not files:
        raise ValueError(f"No files found in {files_directory}, using pattern {file_pattern}")

    # Collect rows + headers in one pass
    rows, headers = collect_rows_and_headers(
        files, header_regex, compiled, event_keyword, show_progress
    )

    # Normalize headers
    headers = ["timestamp"] + \
        [h for h in headers if h not in ("time", "timestamp")]

    # Write CSV if data was found
    if rows:
        count = write_csv(output_csv, headers, rows)
        print(f"\nDone. {count} rows written to {output_csv}")
        # Convert to excel
        output_excel =  output_csv.with_suffix(".xlsx")
        convert_csv_to_excel(output_csv, output_excel)
    else:
        print("No matches found, nothing to write.")
