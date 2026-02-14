from PySide6.QtWidgets import QCheckBox
from PySide6.QtGui import QTextOption
from PySide6.QtCore import Slot
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import MainWindow
    
class CheckboxHandler:
    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window
        self.ui = main_window.ui
        
    def connect_signals(self) -> None:
        self.ui.checkbox_log_preview_wrap_text.checkStateChanged.connect(self.set_file_preview_output_wrap_text)
        
    def set_file_preview_output_wrap_text(self) -> None:
        file_preview_output = self.ui.text_edit_log_preview
        checked_state = self.ui.checkbox_log_preview_wrap_text.isChecked()
        
        if checked_state:
            file_preview_output.setWordWrapMode(QTextOption.WordWrap)
        else:
            file_preview_output.setWordWrapMode(QTextOption.NoWrap)