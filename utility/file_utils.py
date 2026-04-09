from pathlib import Path
from typing import TextIO

# ========== I/O ==========

def validate_input(file: Path | str) -> bool:
    try:
        # First check if file is not None
        if not file:
            raise ValueError("No file provided for processing.")
        
        if isinstance(file, str):
            file = Path(file)
            
        # If not None, check if file exists
        if not file.exists():
            raise FileNotFoundError(f"The specified file '{file}' does not exist.")
        else:
            return True
    except FileNotFoundError:
        return False


def count_lines(file: Path) -> int:
    # Source - https://stackoverflow.com/a/9631635
    # Posted by glglgl, modified by community. See post 'Timeline' for change history
    # Retrieved 2026-04-07, License - CC BY-SA 3.0

    def blocks(file: TextIO, size: int = 65536):
        while True:
            b = file.read(size)
            if not b: 
                break
            yield b
            
    with open(file, "rb") as f:
        return sum(bl.count(b"\n") for bl in blocks(f))


def get_files_in_folder(directory: Path | str, file_pattern: str = "*.log") -> list[Path]:
    """Get files from a directory, of specific type

    Args:
        directory (Path): Path to the folder that contains files
        file_pattern (str, optional): Only get files that match this pattern. Defaults to "*.log".

    Returns:
        list[Path]: List of found files in the directory.
    """
    if isinstance(directory, str):
        directory = Path(directory)
        
    if directory.is_dir() and directory.exists():
        return list(directory.glob(file_pattern))


def create_directory(directory: Path | str):
    if isinstance(directory, str):
        directory = Path(directory)
    
    Path.mkdir(directory.parent, exist_ok=True)
    print(f"Created directory successfully: '{directory.__str__()}'")