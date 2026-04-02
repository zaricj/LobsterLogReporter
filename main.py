from pathlib import Path
from utility.pipeline import run_pipeline

if __name__ == "__main__":
    
    PATTERNS_CONFIG = Path("patterns/patterns.json")
    PATTERN_KEY = "sql_exceptions"
    FILE_PATTERN = "*.log"
    LOGS_PATH = Path("logs")
    CSV_FILE = Path("CSV_Results.csv")
    
    run_pipeline(
        patterns_config=PATTERNS_CONFIG,
        pattern_key=PATTERN_KEY,
        logs_path=LOGS_PATH,
        file_pattern=FILE_PATTERN,
        output_csv=CSV_FILE,
        event_keyword="",
        headers_mode="auto"
    )