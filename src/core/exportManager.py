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
        # Enhanced CSV export with proper encoding
        self.signals.statusbar_message.emit("Exporting to CSV...", 10000)

    def export_to_excel(self, data: pd.DataFrame, filepath: str):
        # Excel export with formatting
        workbook = xlsxwriter.Workbook(filepath)
        worksheet = workbook.add_worksheet()

        # Add formatting
        header_format = workbook.add_format(
            {'bold': True, 'bg_color': '#f0f0f0'})
        # ... apply formatting
