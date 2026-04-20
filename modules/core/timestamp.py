import re
from pathlib import Path
from datetime import datetime

_MONTH_MAP = {
    "Jan": "Jan", "Feb": "Feb", "Mar": "Mär", "Apr": "Apr",
    "May": "Mai", "Jun": "Jun", "Jul": "Jul", "Aug": "Aug",
    "Sep": "Sep", "Oct": "Okt", "Nov": "Nov", "Dec": "Dez"
}

_DATETIME_FORMATS = [
    "%d-%b-%Y %H:%M:%S.%f",   # 19-Jan-2026 06:48:33.088  (Tomcat SEVERE)
    "%d-%b-%Y %H:%M:%S",      # 19-Jan-2026 06:48:33
    "%Y-%m-%dT%H:%M:%S,%f",   # 2026-01-19T07:33:23,289   (ISO 8601, comma ms)
    "%Y-%m-%dT%H:%M:%S.%f",   # 2026-01-19T07:33:23.289   (ISO 8601, dot ms)
    "%Y-%m-%dT%H:%M:%S",      # 2026-01-19T07:33:23
    "%Y-%m-%d %H:%M:%S,%f",   # 2026-01-19 07:33:23,289
    "%Y-%m-%d %H:%M:%S.%f",   # 2026-01-19 07:33:23.289
    "%Y-%m-%d %H:%M:%S",      # 2026-01-19 07:33:23
]

# Patterns that represent a FULL datetime (date + time already present)
_FULL_DATETIME_PATTERNS = [
    # 19-Jan-2026 06:48:33.088
    re.compile(r"\d{1,2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2}:\d{2}"),
    # 2026-01-19T07:33:23,289  or  2026-01-19 07:33:23
    re.compile(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}"),
    # Add more formats if needed
]

# Matches a bare time: 06:48:33 or 06:48:33.088 or 06:48:33,289
_TIME_ONLY_RE = re.compile(r"^\d{2}:\d{2}:\d{2}")


def is_full_datetime(time_str: str) -> bool:
    """Return True if the string already contains a date component."""
    return any(p.search(time_str) for p in _FULL_DATETIME_PATTERNS)


def extract_date_from_filename(filepath: Path) -> str:
    """Extract a date string from the filename (YYYY-MM-DD / YYYY_MM_DD)."""
    date_regex = re.compile(r"\d{4}[-_.]\d{2}[-_.]\d{2}")
    match = date_regex.search(filepath.with_suffix("").name)
    if match:
        date = match.group().replace("_", "-").replace(".", "-")
        return date  # keep as YYYY-MM-DD for consistency
    return ""


def to_german_datetime(time_str: str) -> str:
    """
    Convert any recognised log datetime string to German format:
        DD. Mon YYYY HH:MM:SS
    Returns the original string unchanged if no format matches.
    """
    t = time_str.strip()
    for fmt in _DATETIME_FORMATS:
        try:
            dt = datetime.strptime(t, fmt)
            month_de = _MONTH_MAP[dt.strftime("%b")]
            return dt.strftime(f"%d. {month_de} %Y %H:%M:%S")
        except ValueError:
            continue
    return t  # pass through — visible in CSV so you notice unknown formats


def build_timestamp(time_str: str, filepath: Path, date_created: str) -> str:
    """
    Resolve the best possible timestamp from the parsed log time value.

    Priority:
      1. time_str already contains a full date+time → use as-is
      2. time_str is time-only → prepend date from filename, else date_created
      3. Fallback → date_created
    """
    t = time_str.strip()

    if is_full_datetime(t):
        return to_german_datetime(t)  # already complete, nothing to add

    if _TIME_ONLY_RE.match(t):
        date = extract_date_from_filename(filepath) or date_created
        return to_german_datetime(f"{date} {t}")

    # Unknown format — still try to attach a date
    date = extract_date_from_filename(filepath) or date_created
    return to_german_datetime(f"{date} {t}") if t else date_created