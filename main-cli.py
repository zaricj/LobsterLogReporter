"""
Every single pattern key in patterns.json must contain a regex with multiple groups that will be used to search in an event block in log file.
This makes sure that a single line contains all the matches from the same event block
"""

from pathlib import Path
import click
from modules.core.pipeline import run_pipeline

@click.command()
@click.option("--patterns_config", type=click.Path(exists=True), required=True)
@click.option("--pattern_key", required=True)
@click.option("--files", type=click.Path(exists=True), required=True)
@click.option("--file_pattern", required=True)
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
