from modules.io.file_utils import (
    get_files_in_folder,
    get_file_info
)

from concurrent.futures import ThreadPoolExecutor

import time
import os

"""
Threading sample usage:

    files = get_files_in_folder("logs")
    
    # Use executor.map() to parallelize work on multiple files
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(file_info, files))
        
    # Do something with the results list
"""

def run_with_threading(func, iterable, max_workers=None) -> list:
    if max_workers is None:
        max_workers = min(32, (os.cpu_count() or 1) * 5)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(func, iterable))


def main():
    # Current core count divided by 2
    max_workers = int(os.cpu_count() / 2) if os.cpu_count() else 1

    TEST_FILES = "logs"
    files = get_files_in_folder(TEST_FILES)
    start = time.time()

    results = run_with_threading(get_file_info, files, max_workers)

    end = time.time()
    total_time = f"{end - start:.2f}"

    print(f"Length of results is: {len(results)}")
    for result in results:
        print(result)

    print(f"\nProcessed {len(results)} files in {total_time} seconds.")


if __name__ == "__main__":
    main()
