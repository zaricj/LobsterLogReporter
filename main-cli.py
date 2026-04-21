"""
Every single pattern key in patterns.json must contain a regex with multiple groups that will be used to search in an event block in log file.
This makes sure that a single line contains all the matches from the same event block
"""

from pathlib import Path
import click
from modules.core.pipeline import run_pipeline
from modules.core.utils import get_pattern_keys

PATTERNS_CONFIG = Path("patterns/patterns.json")

@click.command()
@click.option("--config", type=click.Path(exists=True), required=True, help="The configuration file path that holds the patterns used for searching")
@click.option("--key", required=True, help=f"The patterns key to use it's settings for searching. Default pattern config available keys: {get_pattern_keys(PATTERNS_CONFIG)}")
@click.option("--files_dir", type=click.Path(exists=True), required=True, help="The directory with the files which will be searched")
@click.option("--file_pattern", required=True, help="The file pattern to only search")
@click.option("--output_csv", type=click.Path(), required=True)
@click.option("--event_keyword", default="", required=False)
@click.option("--show_progress", type=bool, default=True)

def main(patterns_config, pattern_key, files, file_pattern, output_csv, event_keyword, show_progress):

    run_pipeline(
        patterns_config=Path(patterns_config),
        pattern_key=pattern_key,
        files_directory=Path(files),
        file_pattern=file_pattern,
        output_csv=Path(output_csv),
        event_keyword=event_keyword,
        show_progress=show_progress
    )


if __name__ == "__main__":
    main()
