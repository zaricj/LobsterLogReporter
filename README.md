# LobsterLogReporter

A log file analysis and pattern extraction tool designed to search through log files and extract specific information using regex patterns.

## Core Functionality

- **Pattern-based Log Parsing**: Uses regex patterns to search through log files and extract specific information
- **Event Block Extraction**: Identifies complete event blocks from log files based on separator patterns
- **Multi-pattern Matching**: Can match multiple patterns within a single event block
- **CSV/Excel Export**: Outputs extracted data to CSV and Excel formats

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    LobsterLogReporter                            │
├──────────────────────────────────────────────────────────────────┤
│  main.py                  │ Entry point, orchestrates pipeline   │
│                           │                                      │
│  modules/                 │                                      │
│  ├─ core/                 │                                      │
│  │  ├─ pipeline.py        │ Main processing logic                │
│  │  └─ parser.py          │ Event block extraction & matching    │
│  │                        │                                      │
│  ├─ io/                   │                                      │
│  │  ├─ converters.py      │ Path/epoch conversions               │
│  │  ├─ exporters.py       │ CSV & Excel output                   │
│  │  └─ file_utils.py      │ File operations & validation         │
│  │                        │                                      │
│  ├─ config/               │                                      │
│  │  └─ config.py          │ Pattern config loading & validation  │
│  │                        │                                      │
│  └─ utils/                │                                      │
│     ├─ thread_executor.py │ Threading utilities                  │
│     └─ utilities.py       │ Pattern loading & compilation        │
├──────────────────────────────────────────────────────────────────┤
│  patterns/patterns.json   │ Regex patterns for different log     │
│  logs/                    │   formats (SQL, DB pool, FTP, etc)   │
│  output/                  │   Results                            │
└──────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Threaded Processing**: Uses `ThreadPoolExecutor` for parallel file processing (up to 32 workers)
- **Progress Tracking**: Optional progress bar with `tqdm`
- **Flexible Pattern Configuration**: JSON-based pattern definitions
- **Multiple Log Formats**: Supports various log formats:
  - SQL exceptions
  - Database pool size exceeded
  - FTP per profile logs
  - HTTP requests (Jasperserver)
  - Catalina output (Jasperserver)

## Usage

```python
run_pipeline(
    patterns_config=PATTERNS_CONFIG,  # patterns/patterns.json
    pattern_key=PATTERN_KEY,          # e.g., "sql_exceptions"
    files_directory=FILES_DIR,        # logs/
    file_pattern=FILE_PATTERN,        # *.log
    output_csv=CSV_FILE,              # output/Result_*.csv
    event_keyword="",                 # Optional filter
    show_progress=True
)
```

## Dependencies

- `tqdm` - Progress bars
- `xlsxwriter` - Excel export

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate it:
   ```bash
   # Windows
   .venv\Scripts\Activate.ps1
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # or install directly from pyproject.toml
   pip install -e .
   ```

## Project Structure

```
LobsterLogReporter/
├── main.py                 # Entry point
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── thread.py               
├── gui/                    # GUI module (if applicable)
│   ├── main.py
│   └── modules.py
├── logs/                   # Input log files
├── output/                 # Output results
├── patterns/
│   └── patterns.json       # Regex patterns configuration
├── modules/
│   ├── __init__.py
│   ├── config/
│   │   └── config.py
│   ├── core/
│   │   ├── parser.py
│   │   └── pipeline.py
│   ├── io/
│   │   ├── converters.py
│   │   ├── exporters.py
│   │   └── file_utils.py
│   └── utils/
│       ├── thread_executor.py # Threading utilities
│       └── utilities.py
```

## Configuration

### patterns/patterns.json

Define regex patterns for different log categories:

```json
{
  "sql_exceptions": {
    "base": {
      "separator": "^(?P<time>\\d{2}:\\d{2}:\\d{2})"
    },
    "patterns": {
      "sql_exception": "(?s)exception on sql statement:..."
    }
  },
  "db_pool_size_exceeded": { ... },
  "ftp_per_profile": { ... },
  "http_requests_jasperserver": { ... },
  "catalina_out_jasperserver": { ... }
}
```

### Available Pattern Keys

- `sql_exceptions` - Extract SQL query, error details, and cause
- `db_pool_size_exceeded` - Extract database pool connection info
- `ftp_per_profile` - Extract FTP job information
- `http_requests_jasperserver` - Extract HTTP request logs
- `catalina_out_jasperserver` - Extract Catalina output logs

## Running the Tool

```bash
# From project root
python main.py
```

## License

MIT License

## Author

Jovan 