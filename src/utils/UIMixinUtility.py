from pathlib import Path
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QPixmap, QIcon, QDesktopServices
from PySide6.QtCore import Slot, QSettings, QUrl

from gui.ui.main.LobsterGeneralLogViewer_ui import Ui_MainWindow
from gui.models.treeViewModel import DirectoryViewer
from gui.models.tableViewModel import ResultsTableWidget

# Path configuration (for pattern handler mainly)
FILE_DIR = Path(__file__).resolve()
ROOT_DIR = FILE_DIR.parents[1] # src Folder
GUI_PATTERN_DIRECTORY: Path = ROOT_DIR / "patterns"
GUI_PATTERN_FILE_PATH: Path = GUI_PATTERN_DIRECTORY / "patterns.json"
GUI_PATTERN_DIRECTORY,
GUI_PATTERN_FILE_PATH

class Mixin:
    """
    Mixin class that provides signal handling interface using specialized handlers.
    Delegates responsibilities to focused handler classes for better separation of concerns.
    """
    # Type hints for attributes accessed in this mixin
    ui: Ui_MainWindow
    # helper: 'HelperMethods'
    # ui_state_manager: 'UIStateManager'
    settings: 'QSettings'
    set_max_threads: int
    
    def initialize_ui_all(self):
        """Initialize all utilities, handlers, ui signals etc...
        """
        self.initialize_views()        # Initialize all the different views like Table and Tree
        self.initialize_utilities()    # Initialize utilities first
        self.initialize_handlers()     # Then handlers (which depend on utilities)
        self.initialize_handler_signals()   # Finally connect signals
        
    def initialize_handlers(self):
        """Initialize all specialized event handlers."""
        from event_handling.buttonEvents import ButtonEventHandler
        from event_handling.comboboxEvents import ComboBoxEventHandler
        from event_handling.lineEditEvents import LineEditHandler
        
        self.button_handler = ButtonEventHandler(self)
        self.combobox_handler = ComboBoxEventHandler(self)
        self.line_edit_handler = LineEditHandler(self)
        
    def initialize_handler_signals(self):
        self.button_handler.connect_signals()
        self.combobox_handler.connect_signals()
        self.line_edit_handler.connect_signals()
        
    def initialize_utilities(self):
        from utils.UIStateManager import UIStateManager
        from utils.helperUtility import HelperMethods
        from utils.patternHandler import PatternHandler
        
        self.helper = HelperMethods(self)
        self.ui_state_manager = UIStateManager(self)
        self.pattern_handler = PatternHandler(self,
            GUI_PATTERN_DIRECTORY,
            GUI_PATTERN_FILE_PATH)

    def initialize_views(self):
        self.dir_viewer = DirectoryViewer(self) # Init the tree view model object
        self.table_results = ResultsTableWidget(self)
        
    @Slot(str, int)
    def handle_export_status_message(self, message: str, duration: int) -> None:
        """Handle status bar messages from export operations."""
        self.ui.statusbar.showMessage(message, duration)
        
    @Slot(str, str, str, str)
    def handle_export_manager_success(self, title: str, message: str, save_as_path: str, app_icon_path: str):
        """Enhanced success handler with 'Open Folder' button"""
        app_icon = QIcon(app_icon_path)
        app_icon_as_pixmap = QPixmap(app_icon_path)
        msg_box = QMessageBox()
        
        msg_box.setIconPixmap(app_icon_as_pixmap)
        msg_box.setWindowIcon(app_icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setInformativeText(f"File saved to:\n{save_as_path}")
        
        # Add custom buttons
        open_folder_btn = msg_box.addButton(
            "Open Folder", 
            QMessageBox.ButtonRole.ActionRole)
        
        open_file_btn = msg_box.addButton(
            "Open File", 
            QMessageBox.ButtonRole.ActionRole)
        
        ok_btn = msg_box.addButton(QMessageBox.StandardButton.Ok)

        # Set OK as default
        msg_box.setDefaultButton(ok_btn)

        # Execute dialog and handle response
        msg_box.exec()
        
        clicked_button = msg_box.clickedButton()
        if clicked_button == open_folder_btn:
            # Open the folder containing the file
            folder_path = str(Path(save_as_path).parent)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
        elif clicked_button == open_file_btn:
            # Open the file directly
            QDesktopServices.openUrl(QUrl.fromLocalFile(save_as_path))