import re
import json
from pathlib import Path

# ========== Load & Compile Patterns ==========

def load_patterns_json(filepath: Path) -> dict[str, str]:
    with filepath.open("r", encoding="utf-8") as f:
        return json.load(f)


def compile_regex(pattern: str, flags=0):
    return re.compile(pattern, flags)


def compile_regex_patterns(category_config: dict):
    """Compile base header + patterns for one category"""
    compiled = {}
    compiled["base"] = {name: re.compile(p) for name, p in category_config.get("base", {}).items()}
    compiled["patterns"] = {name: re.compile(p, re.MULTILINE | re.DOTALL) 
                            for name, p in category_config.get("patterns", {}).items()}
    return compiled

# ========== Utility ==========

def yield_event_block(filepath: str | Path, header_pattern: str | re.Pattern):
    
    if isinstance(header_pattern, str):
        header_pattern = re.compile(header_pattern)
        
    buffer = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if header_pattern.match(line):
                if buffer:
                    yield "".join(buffer)
                    buffer.clear()
                    
            # Ignore keywords can be added here, for now the text "at" will be ignored
            #if line.startswith("at"):
            #    continue

            buffer.append(line)

        if buffer:
            yield "".join(buffer)
            


def extract_event_fields(event_block: str, compiled_patterns: dict):
    """Extract fields using compiled regexes"""
    row = {}

    # Extract base info (timestamp, source)
    for name, regex in compiled_patterns["base"].items():
        match = regex.search(event_block)
        if match:
            row.update(match.groupdict())

    # Extract specific patterns (SQL query, error details, parameters)
    for name, regex in compiled_patterns["patterns"].items():
        match = regex.search(event_block)
        if match:
            row.update(match.groupdict())
        else:
            row[name] = "None"  # maintain column consistency

    return row


def get_csv_headers_from_sample(filename: str | Path, header_regex: re.Pattern, compiled_regex: dict) -> list[str]:
    headers = set()
    
    # Get headers from sample
    for block in yield_event_block(filename, header_regex):
        if not is_sql_event(block):
            continue
        
        row = extract_event_fields(block, compiled_regex)
        headers.update(row.keys())
    
    print(f"Headers grabbed from sample: {headers}")
    return list(headers)


def get_files_in_folder(directory: Path, file_pattern: str = "*.log") -> list[Path]:
    """Get files from a directory, of specific type

    Args:
        directory (Path): Path to the folder that contains files
        file_pattern (str, optional): Only get files that match this pattern. Defaults to "*.log".

    Returns:
        list[Path]: List of found files in the directory.
    """
    if directory.is_dir() and directory.exists():
        return list(directory.glob(file_pattern))


def is_sql_event(event: str) -> bool:
    """Use this to only get SQL Exception from the log file

    Args:
        event (str): Event text block in the log file

    Returns:
        bool: True if SQL event, False otherwise
    """
    return "sql" in event.lower()


def clean_block(block: str, ignore_regex: re.Pattern) -> str:
    block = ignore_regex.sub("", block)
    block = re.sub(r"\n{2,}", "\n", block)
    return block.strip()