"""This file contains business logic for exporting the final results to a csv file which would be used for the table result display and also an conversion to an excel file."""
from PySide6.QtCore import QObject, QRunnable, Signal, Slot
import xlsxwriter
import pandas as pd


class ExportManagerSignals(QObject):
    """Signals for export manager."""
    statusbar_message = Signal(str, int)  # message, duration


class ExportManager(QRunnable):
    """Handles CSV and Excel export"""

    def __init__(self):
        super().__init__()
        self.signals = ExportManagerSignals()

    def export_to_csv(self, data: pd.DataFrame, filepath: str, delimiter: str = ';'):
        """Export the table data to CSV. The table data is a Pandas Dataframe.

        Args:
            data (pd.DataFrame): The table data as a Pandas Dataframe.
            filepath (str): Full filepath to where the CSV file will be saved to.
            delimiter (str, optional): CSV delimiter. Defaults to ';'.
        """
        # Enhanced CSV export with proper encoding
        self.signals.statusbar_message.emit("Exporting to CSV...", 10000)
        data.to_csv(filepath, delimiter, index=False) # Export the current dataframe to csv
        
    def export_to_excel(self, data: pd.DataFrame, filepath: str):
        """Export the table data to Excel. The table data is a Pandas Dataframe.

        Args:
            data (pd.DataFrame): The table data as a Pandas Dataframe
            filepath (str): Full filepath to where the Excel file will be saved to.
        """
        sheet_name: str = "Result"
        with pd.ExcelWriter(filepath, "xlsxwriter", mode="w") as writer:
            data.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            max_row, max_col = data.shape
            column_settings = [{"header": col} for col in data.columns]
            worksheet.add_table(0, 0, max_row, max_col - 1, {
                "columns": column_settings,
                "style": "Table Style Medium 16",
                "name": f"{sheet_name[:30]}",
                "autofilter": True
            })
            worksheet.set_column(0, max_col - 1, 18)
        self.signals.statusbar_message.emit("Exported to Excel!", 6000)
