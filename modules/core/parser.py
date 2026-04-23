import re
from typing import Dict

# ========== Utility ==========

def yield_event_block(filepath, separator_pattern, progress=None, task_id=None):
    if isinstance(separator_pattern, str):
        separator_pattern = re.compile(separator_pattern)

    buffer = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            # Update the progress bar every line
            if progress and task_id is not None:
                progress.advance(task_id)

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
