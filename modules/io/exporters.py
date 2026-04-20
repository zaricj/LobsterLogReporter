import csv
import xlsxwriter
from pathlib import Path
from typing import Iterator
from rich.console import Console

from modules.io.file_utils import validate_file, create_directory

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

def convert_csv_to_excel(input_csv_file: Path, output_excel_file: Path) -> str:
    # Validate csv input file
    is_csv_valid = validate_file(input_csv_file)

    if is_csv_valid:
        with Console().status("Converting CSV to Excel, please wait...", spinner="arc"):
            # Create a new Excel workbook and add a worksheet
            workbook = xlsxwriter.Workbook(str(output_excel_file))
            worksheet = workbook.add_worksheet("Data")
            number_format = workbook.add_format({"num_format": "#,##0"})
            
            # Open the CSV file and read 
            # its contents using the csv module
            # Use newline="" so the csv module
            # can handle newlines correctly
            
            with open(input_csv_file, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter=";", quotechar='"')
                for row_idx, row in enumerate(reader):
                    for col_idx, cell in enumerate(row):
                        # Try to write as number
                        # if possible else as string
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
            return f"Converted to Excel as: {output_excel_file}"
    else:
        raise FileNotFoundError("Invalid input file. Please provide a valid CSV file path.")
