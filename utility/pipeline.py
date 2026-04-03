import csv
from pathlib import Path
from typing import Iterator

from utility.core import (
    load_patterns_json,
    compile_regex_patterns,
    get_files_in_folder,
    validate_input
)

from utility.parser import (
    get_csv_headers_from_sample,
    yield_event_block,
    extract_event_fields,
    is_keyword_event,
    extract_log_date
)


# ---------- Config ----------

def load_config(patterns_config: Path, pattern_key: str):
    if not validate_input(patterns_config):
        raise FileNotFoundError(patterns_config)

    patterns_json = load_patterns_json(patterns_config)

    if pattern_key not in patterns_json:
        raise ValueError(f"Invalid key: {pattern_key}")

    compiled = compile_regex_patterns(patterns_json[pattern_key])
    header_regex = compiled["base"]["header"]

    return compiled, header_regex


# ---------- Row Generator ----------

def iter_rows(files: list[Path], header_regex, compiled, keyword: str) -> Iterator[dict]:
    # Identify the specific keys we are looking for in the patterns
    data_keys = compiled["patterns"].keys() 

    for file in files:
        log_date = extract_log_date(file)
        print(f"Processing: {file}") 

        for block in yield_event_block(file, header_regex): 
            if keyword and not is_keyword_event(keyword, block): 
                continue

            row = extract_event_fields(block, compiled) 

            # If every data field (sql_query, error_details, etc.) is None, 
            # it means this block is just a log header or noise. Skip it.
            if all(row.get(key) is None for key in data_keys):
                continue

            # combine date + time
            if "time" in row: 
                timestamp_str = f"{log_date} {row['time']}" 
                row["timestamp"] = timestamp_str.strip() # Remove whitespace at the beginning if no log_date was found
                del row["time"] 

            yield row 


# ---------- CSV ----------

def write_csv(output: Path, headers: list[str], rows: Iterator[dict]) -> int:
    count = 0

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=headers,
            delimiter=";",
            quotechar='"',
            quoting=csv.QUOTE_ALL
        )

        writer.writeheader()

        for row in rows:
            normalized = {k: row.get(k, "") for k in headers}
            writer.writerow(normalized)
            count += 1

    return count


# ---------- Pipeline ----------

def run_pipeline(
    patterns_config: Path,
    pattern_key: str,
    logs_path: Path,
    file_pattern: str,
    output_csv: Path,
    event_keyword: str = "",
    headers_mode: str = "auto"
):
    compiled, header_regex = load_config(patterns_config, pattern_key)

    files = get_files_in_folder(logs_path, file_pattern)

    if not files:
        raise ValueError("No log files found")

    # Headers
    if headers_mode == "auto":
        headers = get_csv_headers_from_sample(
            files[0], header_regex, compiled, event_keyword
        )
    else:
        headers = list(compiled["patterns"].keys())
    
    # Remove the time header from the base header key
    headers = [h for h in headers if h != "time"]
    headers.insert(0, "timestamp")

    # Rows
    rows = iter_rows(files, header_regex, compiled, event_keyword)

    # Write
    count = write_csv(output_csv, headers, rows)

    print(f"\nDone. {count} rows written to {output_csv}")


def run_test(
    patterns_config: Path,
    pattern_key: str,
    sample_file: Path,
    output_csv: Path,
    event_keyword: str = "",
    headers_mode: str = "auto"
):
    from pprint import pprint
    
    test_file = [sample_file]
    pprint("Running test pipeline.")
    
    pprint("Loading patterns configuration...")
    compiled, header_regex = load_config(patterns_config, pattern_key)
    
    pprint("Compiled patterns:")
    for c_key, c_value in compiled.items():
        pprint(f"{c_key}: {c_value}")

    pprint("Compiled headers:")
    pprint(header_regex)
    
    
    if not sample_file:
        raise ValueError("File not found")

    # Headers
    if headers_mode == "auto":
        pprint("Getting headers from sample...")
        headers = get_csv_headers_from_sample(
            sample_file, header_regex, compiled, event_keyword
        )
    else:
        pprint("Using specified headers...")
        headers = list(compiled["patterns"].keys())
    
    pprint(f"GRABBED HEADERS: {headers}")
    
    # Remove the time header from the base header key
    headers = [h for h in headers if h != "time"]
    headers.insert(0, "timestamp")
    
    pprint(f"Headers after trying to remove the 'time' header: {headers}")

    pprint("Iterating over rows...")
    # Rows
    rows = iter_rows(test_file, header_regex, compiled, event_keyword)

    # Write
    count = write_csv(output_csv, headers, rows)

    print(f"\nDone. {count} rows written to {output_csv}")