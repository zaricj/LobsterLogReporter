from pathlib import Path
from utility.pipeline import run_pipeline
from utility.patterns import get_pattern_keys

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
        pattern_key="db_pool_size_exceeded",
        files_directory=FILES_DIR,
        file_pattern=FILE_PATTERN,
        output_csv=CSV_FILE,
        event_keyword="",
        show_progress=True
    )
