import re
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from typing import (Iterator, Dict)

from modules.io.file_utils import count_lines


# ========== Utility ==========

def yield_event_block(filepath: str | Path, separator_pattern: str | re.Pattern):
    """Yields the files event block, using a separator pattern

    Args:
        filepath (str | Path): The file to read and yield event blocks from
        separator_pattern (str | re.Pattern): The pattern to identify the start of an event block.

    Yields:
        str: Yields a block of text, starting from the first matching separator pattern until the next one.
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

            buffer.append(line)

        if buffer:
            yield "".join(buffer)


def yield_event_block_with_progress(
    filepath: Path,
    separator_pattern: re.Pattern,
) -> Iterator[str]:

    if isinstance(separator_pattern, str):
        separator_pattern = re.compile(separator_pattern)

    with open(filepath, "r", encoding="utf-8") as f:
        total_lines = count_lines(filepath)
        buffer: list[str] = []

        for line in tqdm(f, total=total_lines, desc=filepath.name):
            if separator_pattern.match(line):
                if buffer:
                    yield "".join(buffer)
                    buffer.clear()
            buffer.append(line)

        if buffer:
            yield "".join(buffer)


def extract_matches_from_event_block(event_block: str, compiled_patterns: dict) -> Dict[str, str]:
    """Extract the matches from the event block of text, with the compiled regex patterns.
    Uses a non-destructive update: later patterns will not overwrite keys already 
    found by earlier patterns.

    Args:
        event_block (str): The text block of the event.
        compiled_patterns (dict): A dictionary of compiled regex patterns.

    Returns:
        dict: A dictionary containing the found matches in the event block.
    """
    row = {}

    # 1. Process "base" patterns (e.g., time/separator info)
    for _, regex in compiled_patterns.get("base", {}).items():
        match = regex.search(event_block)
        if match:
            for key, value in match.groupdict().items():
                # Only set if the key is new or current value is empty
                if value and not row.get(key):
                    row[key] = value

    # 2. Process "patterns" (the specific match extractors)
    for _, regex in compiled_patterns.get("patterns", {}).items():
        match = regex.search(event_block)
        if match:
            new_data = match.groupdict()
            for key, value in new_data.items():
                # NON-DESTRUCTIVE: Keep the first non-empty value found
                # If match was found by pattern A, pattern B won't overwrite it.
                if value and not row.get(key):
                    row[key] = value

    return row


def extract_log_date(filepath: Path) -> str:
    date = ""

    # Try first from the file name, if the filename contains a date
    # Matches the patterns: 2026-04-13, 2026_04_13
    date_regex = re.compile(r"\d{4}[-_.]\d{2}[-_.]\d{2}")
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


def clean_block(block: str, ignore_regex: re.Pattern) -> str:
    block = ignore_regex.sub("", block)
    block = re.sub(r"\n{2,}", "\n", block)
    return block.strip()
