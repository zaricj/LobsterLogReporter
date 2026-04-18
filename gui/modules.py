from pathlib import Path
from datetime import datetime
import re
import csv
import xlsxwriter
import json
from typing import Iterator, TextIO, Dict

# ========== Utility ==========


def yield_event_block(filepath: str | Path, separator_pattern: str | re.Pattern):
    """Yields the files event block, using a separator pattern

    Args:
        filepath (str | Path): The file to read and yield event blocks from
        separator_pattern (str | re.Pattern): The pattern to identify the start of an event block

    Yields:
        str: The text block of the event
    """

    if isinstance(separator_pattern, str):
        separator_pattern = re.compile(separator_pattern)

    buffer = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if separator_pattern.match(line):
                if buffer:
                    yield "".join(buffer)
                    buffer.clear()

            # Ignore keywords can be added here, for now the text "at" will be ignored
            # if line.startswith("at"):
            #    continue

            buffer.append(line)

        if buffer:
            yield "".join(buffer)


def extract_matches_from_event_block(
    event_block: str, compiled_patterns: dict
) -> Dict[str, str]:
    """Extract the matches from the event block of text, with the compiled regex patterns.

    Args:
        event_block (str): The text block of the event, which contains all the info we want to extract from.
        compiled_patterns (dict): A dictionary of compiled regex patterns.

    Returns:
        dict: A dictionary containing the found matches in the event block.
    """
    row = {}

    # Base (e.g. time)
    for _, regex in compiled_patterns["base"].items():
        match = regex.search(event_block)
        if match:
            row.update(match.groupdict())

    # Patterns
    for _, regex in compiled_patterns["patterns"].items():
        match = regex.search(event_block)
        if match:
            row.update(match.groupdict())

    return row


def extract_log_date(filepath: Path) -> str:
    date = ""

    # Try first from the file name, if the filename contains a date
    date_regex = re.compile(r"\d{4}_\d{2}_\d{2}")
    match = date_regex.search(filepath.with_suffix("").name)

    if match:
        date = match.group()
        if "_" in date:  # Replace underlines with dots in date string
            date = date.replace("_", ".")
        return date

    # Else if none was found continue from within the file, usually if it's a log file it has a date in the beginning
    date_regex = re.compile(r"opened at (?P<date>.+?\d{4})")

    with open(filepath, "r", encoding="utf-8") as f:
        for _ in range(10):  # only scan first lines
            line = f.readline()
            if not line:
                break

            match = date_regex.search(line)

            if match:
                raw_date = match.group("date")
                cleaned_date = re.sub(r"\b[A-Z]{3,4}\b", "", raw_date).strip()

                dt = datetime.strptime(cleaned_date, "%a %b %d %H:%M:%S %Y")
                date = dt.strftime("%Y-%m-%d")
                # Return ISO date
                return date

    return date


def is_keyword_event(keyword: str, event_block: str) -> bool:
    """Use this to filter out event blocks that contain a specific keyword

    Args:
        keyword (str): Keyword to look for in event block
        event_block (str): Event text block in the log file

    Returns:
        bool: True if keyword is in the event block, False otherwise
    """
    return keyword.lower() in event_block.lower()


# ========== Config ==========


def load_config(patterns_config: Path, pattern_key: str) -> tuple[dict, re.Pattern]:
    if not validate_file(patterns_config):
        raise FileNotFoundError(patterns_config)

    patterns_json = load_patterns_json(patterns_config)

    if pattern_key not in patterns_json:
        raise ValueError(f"Invalid key: {pattern_key}")

    compiled = compile_regex_patterns(patterns_json[pattern_key])
    separator_regex = compiled["base"]["separator"]

    return compiled, separator_regex


# ========== CSV ==========


def write_csv(output: Path, headers: list[str], rows: Iterator[dict]) -> int:
    """Writes rows to a CSV file with the specified headers.

    Args:
        output (Path): The path to the output CSV file.
        headers (list[str]): A list of column headers for the CSV.
        rows (Iterator[dict]): An iterator over dictionaries representing each row.

    Returns:
        int: The number of rows written to the CSV file.
    """
    count = 0

    if not output.parent.exists():
        create_directory(output)

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=headers, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL
        )

        writer.writeheader()

        for row in rows:
            normalized = {k: row.get(k, "") for k in headers}
            writer.writerow(normalized)
            count += 1

    return count


# ========== Excel Conversion ==========


def convert_csv_to_excel(input_csv_file: Path, output_excel_file: Path):
    # Validate csv input file
    is_csv_valid = validate_file(input_csv_file)

    if is_csv_valid:
        print("Converting CSV to Excel, please wait...")
        # Create a new Excel workbook and add a worksheet
        workbook = xlsxwriter.Workbook(str(output_excel_file))
        worksheet = workbook.add_worksheet("Data")
        number_format = workbook.add_format({"num_format": "#,##0"})
        # Open the CSV file and read its contents using the csv module
        # Use newline="" so the csv module can handle newlines correctly
        with open(input_csv_file, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=";", quotechar='"')
            for row_idx, row in enumerate(reader):
                for col_idx, cell in enumerate(row):
                    # Try to write as number if possible, else as string
                    try:
                        # Attempt to convert to int
                        num_value = int(cell)
                        worksheet.write_number(
                            row_idx, col_idx, num_value, number_format
                        )
                    except ValueError:
                        # If not a number, write as string
                        worksheet.write(row_idx, col_idx, cell)
        workbook.close()
        print(f"Excel written: {output_excel_file}")
    else:
        print("Invalid input file. Please provide a valid CSV file path.")


# ========== I/O ==========


def validate_file(file: Path | str) -> bool:
    try:
        # First check if file is not None
        if not file:
            raise ValueError("No file provided for processing.")

        if isinstance(file, str):
            file = Path(file)

        # If not None, check if file exists
        if not file.exists():
            raise FileNotFoundError(f"The specified file '{file}' does not exist.")
        else:
            return True
    except FileNotFoundError:
        return False


def count_lines(file: Path) -> int:
    # Source - https://stackoverflow.com/a/9631635
    # Posted by glglgl, modified by community. See post 'Timeline' for change history
    # Retrieved 2026-04-07, License - CC BY-SA 3.0

    def blocks(file: TextIO, size: int = 65536):
        while True:
            b = file.read(size)
            if not b:
                break
            yield b

    with open(file, "rb") as f:
        return sum(bl.count(b"\n") for bl in blocks(f))


def get_files_in_folder(
    directory: Path | str, file_pattern: str = "*.log"
) -> list[Path]:
    """Get files from a directory, of specific type

    Args:
        directory (Path): Path to the folder that contains files
        file_pattern (str, optional): Only get files that match this pattern. Defaults to "*.log".

    Returns:
        list[Path]: List of found files in the directory.
    """
    if isinstance(directory, str):
        directory = Path(directory)

    if directory.is_dir() and directory.exists():
        return list(directory.glob(file_pattern))


def create_directory(directory: Path | str):
    if isinstance(directory, str):
        directory = Path(directory)

    Path.mkdir(directory.parent, exist_ok=True)
    print(f"Created directory successfully: '{directory.__str__()}'")


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
    compiled["base"] = {
        name: re.compile(p) for name, p in category_config.get("base", {}).items()
    }
    compiled["patterns"] = {
        name: re.compile(p, re.MULTILINE | re.DOTALL)
        for name, p in category_config.get("patterns", {}).items()
    }
    return compiled


# ========== Rows and headers Generator ==========


def collect_rows_and_headers(
    files: list,
    separator_regex,
    compiled,
    keyword: str,
):
    headers = []
    rows = []

    for file in files:
        log_date = extract_log_date(file)
        print(f"Processing: {file}")

        for block in yield_event_block(file, separator_regex):
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
            if not any(v not in (None, "") for k, v in row.items() if k != "timestamp"):
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
):

    compiled, separator_regex = load_config(patterns_config, pattern_key)

    files = get_files_in_folder(files_directory, file_pattern)

    if not files:
        raise ValueError(
            f"No files found in {files_directory}, using pattern {file_pattern}"
        )

    # Collect rows + headers in one pass
    rows, headers = collect_rows_and_headers(
        files, separator_regex, compiled, event_keyword
    )

    # Normalize headers
    headers = ["timestamp"] + [h for h in headers if h not in ("time", "timestamp")]

    # Write CSV if data was found
    if rows:
        count = write_csv(output_csv, headers, rows)
        print(f"\nDone. {count} rows written to {output_csv}")
        # Convert to excel
        output_excel = output_csv.with_suffix(".xlsx")
        convert_csv_to_excel(output_csv, output_excel)
    else:
        print("No matches found, nothing to write.")


if __name__ == "__main__":
    PATTERNS_CONFIG = Path("patterns/patterns.json")
    PATTERN_KEY = "sql_exceptions"
    FILE_PATTERN = "*.log"
    FILES_DIR = Path("logs")

    # CSV output
    OUTPUT_DIR = Path("output")
    CSV_FILE = OUTPUT_DIR / "Result.csv"

    # Test run config
    SAMPLE_FILE = Path("sample.log")

    # TODO Every single pattern key in patterns.json must contain a regex with multiple groups that will be used to search in an event block in log file.
    # TODO This makes sure that a single line contains all the matches from the same even block

    # Load all pattern config keys
    # patterns = get_pattern_keys(PATTERNS_CONFIG)

    run_pipeline(
        patterns_config=PATTERNS_CONFIG,
        pattern_key="ftp_per_profile",
        files_directory=r"C:\Users\ZaricJ\Downloads\FTP Per Profile",
        file_pattern=FILE_PATTERN,
        output_csv=CSV_FILE,
        event_keyword="",
        show_progress=True,
    )
