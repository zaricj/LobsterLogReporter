"""Centralized signal connection management."""
from typing import TYPE_CHECKING
from core.exportManager import ExportManager
from core.fileParser import FileParserWorker

if TYPE_CHECKING:
    from app import MainWindow


class SignalConnector:
    """Manages signal connections for worker threads."""

    def __init__(self, main_window: 'MainWindow'):
        self.main_window = main_window
        self.ui = main_window.ui

    def connect_table_data_exporter(self, worker: ExportManager):
        """Connect signals for XML parsing operations."""
        worker.signals.statusbar_message.connect(
            self.main_window.handle_statusbar_show_message)

    def connect_file_parser_worker(self, worker: FileParserWorker):
        """Connect signals for the file parser operator

        Args:
            worker (FileParserWorker): FileParserWorker thread object
        """
        worker.signals.set_text_output.connect(
            self.main_window.handle_text_edit_append)
