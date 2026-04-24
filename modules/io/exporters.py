import csv
import pandas as pd
from pathlib import Path
from typing import Iterator
from modules.core.ui import CONSOLE

from modules.io.file_utils import ensure_output_dir

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
        ensure_output_dir(output)

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
    if not input_csv_file.exists():
        raise FileNotFoundError("Invalid input file.")

    with CONSOLE.status("[bold]>>> Converting CSV to Excel...[/bold]", spinner="arc"):
        # read_csv is significantly faster than the csv module for large files
        df = pd.read_csv(
            input_csv_file, 
            sep=';', 
            quotechar='"', 
            encoding='utf-8',
            engine='c'
        )

        # to_excel handles all type conversions (ints, floats, strings) natively
        df.to_excel(output_excel_file, index=False, engine='xlsxwriter')
