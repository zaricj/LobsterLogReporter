"""
Log Parser GUI
==============
A Tkinter-based GUI front-end for the modules.py log-parsing pipeline.

Requires (same dependencies as the original script):
    pip install xlsxwriter

Usage:
    python log_parser_gui.py
"""

from __future__ import annotations

import json
import queue
import re
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

# ---------------------------------------------------------------------------
# Attempt to import the business-logic layer.
# If the file lives next to this script it is imported directly; otherwise
# every function is inlined so this file stays self-contained.
# ---------------------------------------------------------------------------
try:
    from gui.modules import (
        compile_regex_patterns,
        convert_csv_to_excel,
        get_files_in_folder,
        get_pattern_keys,
        load_patterns_json,
        run_pipeline,
        validate_input,
    )
    _CORE_IMPORTED = True
except ImportError:
    _CORE_IMPORTED = False
    # ---- inline stubs so the GUI still opens without the core module -------
    from datetime import datetime

    def load_patterns_json(filepath: Path) -> dict:
        with filepath.open("r", encoding="utf-8") as f:
            return json.load(f)

    def get_pattern_keys(filepath: Path) -> list[str]:
        return list(load_patterns_json(filepath).keys())

    def compile_regex_patterns(category_config: dict) -> dict:
        compiled: dict = {}
        compiled["base"] = {
            name: re.compile(p)
            for name, p in category_config.get("base", {}).items()
        }
        compiled["patterns"] = {
            name: re.compile(p, re.MULTILINE | re.DOTALL)
            for name, p in category_config.get("patterns", {}).items()
        }
        return compiled

    def validate_input(file) -> bool:
        try:
            if not file:
                return False
            p = Path(file)
            return p.exists()
        except Exception:
            return False

    def get_files_in_folder(directory, file_pattern="*.log") -> list[Path]:
        d = Path(directory)
        if d.is_dir():
            return list(d.glob(file_pattern))
        return []

    def run_pipeline(
        patterns_config,
        pattern_key,
        files_directory,
        file_pattern,
        output_csv,
        event_keyword="",
        show_progress=False,
    ):
        # Minimal stub — real logic lives in modules.py
        raise RuntimeError(
            "modules.py could not be imported. "
            "Place it next to this script and restart."
        )


# ---------------------------------------------------------------------------
# Colour / style palette
# ---------------------------------------------------------------------------
PAL = {
    "bg":        "#1a1a1e",   # deep navy background
    "panel":     "#242429",   # slightly lighter card
    "border":    "#323237",   # subtle borders
    "accent":    "#268954",   # electric blue accent
    "accent2":   "#3666c0",   # aquamarine highlight
    "text":      "#fefefe",   # near-white body text
    "muted":     "#8d9096",   # de-emphasised text
    "success":   "#16a34a",   # green status
    "warn":      "#f59e0b",   # amber warning
    "error":     "#dc2626",   # red error
    "entry_bg":  "#3f4044",   # input field bg
    "btn":       "#268954",   # primary button
    "btn_hover": "#227147",
    "btn_text":  "#fefefe",
}

FONT_MONO  = ("Courier New", 9)
FONT_BODY  = ("Segoe UI", 10)
FONT_LABEL = ("Segoe UI", 10, "bold")
FONT_H1    = ("Segoe UI", 14, "bold")
FONT_H2    = ("Segoe UI", 11, "bold")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _styled_entry(parent, textvariable=None, width=40, **kw) -> tk.Entry:
    e = tk.Entry(
        parent,
        textvariable=textvariable,
        width=width,
        bg=PAL["entry_bg"],
        fg=PAL["text"],
        insertbackground=PAL["accent"],
        relief="flat",
        bd=0,
        font=FONT_BODY,
        **kw,
    )
    # thin highlight border via a frame wrapper (done at call-site)
    return e


def _frame_border(parent, **kw) -> tk.Frame:
    """A 1-px border wrapper frame."""
    outer = tk.Frame(parent, bg=PAL["border"], padx=1, pady=1, **kw)
    inner = tk.Frame(outer, bg=PAL["entry_bg"])
    inner.pack(fill="both", expand=True)
    return outer, inner


def _section_label(parent, text: str) -> tk.Label:
    lbl = tk.Label(
        parent,
        text=text,
        bg=PAL["panel"],
        fg=PAL["accent2"],
        font=FONT_H2,
        anchor="w",
    )
    return lbl


def _label(parent, text: str, muted=False) -> tk.Label:
    return tk.Label(
        parent,
        text=text,
        bg=PAL["panel"],
        fg=PAL["muted"] if muted else PAL["text"],
        font=FONT_BODY,
        anchor="w",
    )


class HoverButton(tk.Button):
    """Button with hover colour change."""

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.config(
            bg=PAL["btn"],
            fg=PAL["btn_text"],
            activebackground=PAL["btn_hover"],
            activeforeground=PAL["btn_text"],
            relief="flat",
            bd=0,
            cursor="hand2",
            font=FONT_LABEL,
            padx=14,
            pady=7,
        )
        self.bind("<Enter>", lambda _: self.config(bg=PAL["btn_hover"]))
        self.bind("<Leave>", lambda _: self.config(bg=PAL["btn"]))


# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------

class LogParserApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Log Parser Pipeline")
        self.configure(bg=PAL["bg"])
        self.resizable(True, True)
        self.minsize(780, 640)

        # ---- state variables ------------------------------------------------
        self.patterns_config_var = tk.StringVar()
        self.pattern_key_var     = tk.StringVar()
        self.files_dir_var       = tk.StringVar()
        self.file_pattern_var    = tk.StringVar(value="*.log")
        self.output_csv_var      = tk.StringVar()
        self.keyword_var         = tk.StringVar()

        self._pattern_keys: list[str] = []
        self._log_queue: queue.Queue  = queue.Queue()
        self._running = False

        self._build_ui()
        self._poll_log_queue()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Top title bar
        title_bar = tk.Frame(self, bg=PAL["bg"], pady=14)
        title_bar.pack(fill="x", padx=20)

        tk.Label(
            title_bar,
            text="⬡  LOG PARSER PIPELINE",
            bg=PAL["bg"],
            fg=PAL["accent"],
            font=FONT_H1,
        ).pack(side="left")

        self._status_dot = tk.Label(
            title_bar, text="●", bg=PAL["bg"], fg=PAL["muted"], font=("Segoe UI", 16)
        )
        self._status_dot.pack(side="right", padx=4)
        self._status_label = tk.Label(
            title_bar, text="Idle", bg=PAL["bg"], fg=PAL["muted"], font=FONT_BODY
        )
        self._status_label.pack(side="right")

        # Divider
        tk.Frame(self, bg=PAL["border"], height=1).pack(fill="x")

        # Main content pane
        content = tk.Frame(self, bg=PAL["bg"])
        content.pack(fill="both", expand=True, padx=18, pady=12)

        # Left config panel
        left = tk.Frame(content, bg=PAL["panel"], bd=0, padx=18, pady=14)
        left.pack(side="left", fill="both", expand=False, padx=(0, 10))
        left.config(highlightbackground=PAL["border"], highlightthickness=1)

        self._build_config_panel(left)

        # Right log panel
        right = tk.Frame(content, bg=PAL["panel"], bd=0, padx=14, pady=14)
        right.pack(side="left", fill="both", expand=True)
        right.config(highlightbackground=PAL["border"], highlightthickness=1)

        self._build_log_panel(right)

        # Bottom run bar
        run_bar = tk.Frame(self, bg=PAL["bg"], pady=10)
        run_bar.pack(fill="x", padx=18)

        self._progress = ttk.Progressbar(
            run_bar, mode="indeterminate", length=300
        )
        self._progress.pack(side="left", padx=(0, 16))

        self._run_btn = HoverButton(
            run_bar, text="▶  Run Pipeline", command=self._start_pipeline
        )
        self._run_btn.pack(side="left")

        self._clear_btn = HoverButton(
            run_bar,
            text="✕  Clear Log",
            command=self._clear_log,
        )
        self._clear_btn.config(bg=PAL["border"])
        self._clear_btn.bind("<Enter>", lambda _: self._clear_btn.config(bg=PAL["muted"]))
        self._clear_btn.bind("<Leave>", lambda _: self._clear_btn.config(bg=PAL["border"]))
        self._clear_btn.pack(side="left", padx=8)

    # --- Config panel -------------------------------------------------------

    def _build_config_panel(self, parent: tk.Frame):
        _section_label(parent, "Configuration").pack(fill="x", pady=(0, 12))

        # Patterns config file
        _label(parent, "Patterns JSON").pack(fill="x")
        row = tk.Frame(parent, bg=PAL["panel"])
        row.pack(fill="x", pady=(2, 10))
        e = _styled_entry(row, textvariable=self.patterns_config_var, width=28)
        e.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 6))
        HoverButton(row, text="…", command=self._browse_patterns, padx=8, pady=4).pack(side="left")
        self.patterns_config_var.trace_add("write", self._on_patterns_file_change)

        # Pattern key dropdown
        _label(parent, "Pattern Key").pack(fill="x")
        self._key_combo = ttk.Combobox(
            parent,
            textvariable=self.pattern_key_var,
            state="readonly",
            font=FONT_BODY,
        )
        self._key_combo.pack(fill="x", pady=(2, 10), ipady=4)
        self._style_combobox()

        # Files directory
        _label(parent, "Logs Directory").pack(fill="x")
        row2 = tk.Frame(parent, bg=PAL["panel"])
        row2.pack(fill="x", pady=(2, 10))
        _styled_entry(row2, textvariable=self.files_dir_var, width=28).pack(
            side="left", fill="x", expand=True, ipady=5, padx=(0, 6)
        )
        HoverButton(row2, text="…", command=self._browse_files_dir, padx=8, pady=4).pack(side="left")

        # File pattern
        _label(parent, "File Pattern").pack(fill="x")
        _styled_entry(parent, textvariable=self.file_pattern_var, width=36).pack(
            fill="x", pady=(2, 10), ipady=5
        )

        # Output CSV
        _label(parent, "Output CSV").pack(fill="x")
        row3 = tk.Frame(parent, bg=PAL["panel"])
        row3.pack(fill="x", pady=(2, 10))
        _styled_entry(row3, textvariable=self.output_csv_var, width=28).pack(
            side="left", fill="x", expand=True, ipady=5, padx=(0, 6)
        )
        HoverButton(row3, text="…", command=self._browse_output_csv, padx=8, pady=4).pack(side="left")

        # Optional keyword filter
        _section_label(parent, "Filter").pack(fill="x", pady=(12, 6))
        _label(parent, "Event Keyword  (optional)").pack(fill="x")
        _styled_entry(parent, textvariable=self.keyword_var, width=36).pack(
            fill="x", pady=(2, 10), ipady=5
        )

        # Pattern info box
        _section_label(parent, "Pattern Preview").pack(fill="x", pady=(12, 6))
        self._pattern_info = tk.Text(
            parent,
            height=7,
            bg=PAL["entry_bg"],
            fg=PAL["muted"],
            font=FONT_MONO,
            relief="flat",
            bd=0,
            wrap="word",
            state="disabled",
        )
        self._pattern_info.pack(fill="x")
        self._key_combo.bind("<<ComboboxSelected>>", self._on_key_selected)

    # --- Log panel ----------------------------------------------------------

    def _build_log_panel(self, parent: tk.Frame):
        _section_label(parent, "Pipeline Output").pack(fill="x", pady=(0, 8))

        self._log_area = scrolledtext.ScrolledText(
            parent,
            bg=PAL["entry_bg"],
            fg=PAL["text"],
            font=FONT_MONO,
            relief="flat",
            bd=0,
            wrap="word",
            state="disabled",
            insertbackground=PAL["accent"],
        )
        self._log_area.pack(fill="both", expand=True)

        # Configure colour tags
        self._log_area.tag_config("info",    foreground=PAL["text"])
        self._log_area.tag_config("success", foreground=PAL["success"])
        self._log_area.tag_config("warn",    foreground=PAL["warn"])
        self._log_area.tag_config("error",   foreground=PAL["error"])
        self._log_area.tag_config("accent",  foreground=PAL["accent"])
        self._log_area.tag_config("muted",   foreground=PAL["muted"])

    # ------------------------------------------------------------------
    # Combobox theme patch
    # ------------------------------------------------------------------

    def _style_combobox(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure(
            "TCombobox",
            fieldbackground=PAL["entry_bg"],
            background=PAL["entry_bg"],
            foreground=PAL["text"],
            arrowcolor=PAL["accent"],
            selectbackground=PAL["accent"],
            selectforeground=PAL["btn_text"],
            borderwidth=0,
        )
        style.map("TCombobox", fieldbackground=[("readonly", PAL["entry_bg"])])
        style.configure("TProgressbar", troughcolor=PAL["border"], background=PAL["accent"])

    # ------------------------------------------------------------------
    # File / directory browsers
    # ------------------------------------------------------------------

    def _browse_patterns(self):
        path = filedialog.askopenfilename(
            title="Select Patterns JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            self.patterns_config_var.set(path)

    def _browse_files_dir(self):
        path = filedialog.askdirectory(title="Select Logs Directory")
        if path:
            self.files_dir_var.set(path)

    def _browse_output_csv(self):
        path = filedialog.asksaveasfilename(
            title="Output CSV file",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.output_csv_var.set(path)

    # ------------------------------------------------------------------
    # Pattern loading
    # ------------------------------------------------------------------

    def _on_patterns_file_change(self, *_):
        """Reload the pattern key dropdown whenever the JSON path changes."""
        path_str = self.patterns_config_var.get().strip()
        if not path_str:
            return

        path = Path(path_str)
        if not path.exists() or not path.is_file():
            return

        try:
            keys = get_pattern_keys(path)
        except Exception as exc:
            self._log(f"[warn] Could not read patterns file: {exc}", "warn")
            return

        self._pattern_keys = keys
        self._key_combo["values"] = keys

        if keys:
            current = self.pattern_key_var.get()
            if current not in keys:
                self.pattern_key_var.set(keys[0])
            self._update_pattern_preview()
            self._log(
                f"Loaded {len(keys)} pattern key(s) from {path.name}", "success"
            )
        else:
            self._log("[warn] Patterns JSON has no keys.", "warn")

    def _on_key_selected(self, *_):
        self._update_pattern_preview()

    def _update_pattern_preview(self):
        """Display the raw regex strings for the selected key in the preview box."""
        path_str = self.patterns_config_var.get().strip()
        key      = self.pattern_key_var.get().strip()
        if not path_str or not key:
            return

        try:
            data = load_patterns_json(Path(path_str))
        except Exception:
            return

        if key not in data:
            return

        category = data[key]
        lines = []
        for section in ("base", "patterns"):
            entries = category.get(section, {})
            if entries:
                lines.append(f"[{section}]")
                for name, pattern in entries.items():
                    lines.append(f"  {name}:")
                    lines.append(f"    {pattern}")
                lines.append("")

        preview_text = "\n".join(lines) if lines else "(no patterns)"

        self._pattern_info.config(state="normal")
        self._pattern_info.delete("1.0", "end")
        self._pattern_info.insert("end", preview_text)
        self._pattern_info.config(state="disabled")

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def _log(self, message: str, tag: str = "info"):
        self._log_area.config(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S") if "datetime" in dir() else ""
        try:
            from datetime import datetime as _dt
            timestamp = _dt.now().strftime("%H:%M:%S")
        except Exception:
            pass
        prefix = f"[{timestamp}]  " if timestamp else ""
        self._log_area.insert("end", prefix + message + "\n", tag)
        self._log_area.see("end")
        self._log_area.config(state="disabled")

    def _clear_log(self):
        self._log_area.config(state="normal")
        self._log_area.delete("1.0", "end")
        self._log_area.config(state="disabled")

    def _poll_log_queue(self):
        """Drain the thread-safe log queue into the text widget."""
        try:
            while True:
                msg, tag = self._log_queue.get_nowait()
                self._log(msg, tag)
        except queue.Empty:
            pass
        self.after(100, self._poll_log_queue)

    def _qlog(self, message: str, tag: str = "info"):
        """Thread-safe logging."""
        self._log_queue.put((message, tag))

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_inputs(self) -> bool:
        errors = []

        p = self.patterns_config_var.get().strip()
        if not p:
            errors.append("• Patterns JSON file is required.")
        elif not Path(p).exists():
            errors.append("• Patterns JSON file does not exist.")

        if not self.pattern_key_var.get().strip():
            errors.append("• Pattern key must be selected.")

        d = self.files_dir_var.get().strip()
        if not d:
            errors.append("• Logs directory is required.")
        elif not Path(d).is_dir():
            errors.append("• Logs directory does not exist.")

        if not self.file_pattern_var.get().strip():
            errors.append("• File pattern is required (e.g. *.log).")

        if not self.output_csv_var.get().strip():
            errors.append("• Output CSV path is required.")

        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return False
        return True

    # ------------------------------------------------------------------
    # Pipeline execution
    # ------------------------------------------------------------------

    def _start_pipeline(self):
        if self._running:
            return
        if not self._validate_inputs():
            return

        # Gather config snapshot
        cfg = {
            "patterns_config": Path(self.patterns_config_var.get().strip()),
            "pattern_key":     self.pattern_key_var.get().strip(),
            "files_directory": Path(self.files_dir_var.get().strip()),
            "file_pattern":    self.file_pattern_var.get().strip(),
            "output_csv":      Path(self.output_csv_var.get().strip()),
            "event_keyword":   self.keyword_var.get().strip(),
        }

        self._running = True
        self._run_btn.config(state="disabled", text="⏳  Running…")
        self._progress.start(12)
        self._set_status("Running", PAL["warn"])
        self._qlog("─" * 50, "muted")
        self._qlog(f"Starting pipeline  [key={cfg['pattern_key']}]", "accent")

        thread = threading.Thread(target=self._run_pipeline_thread, args=(cfg,), daemon=True)
        thread.start()

    def _run_pipeline_thread(self, cfg: dict):
        import io
        import sys

        class _Redirector(io.TextIOBase):
            def __init__(self_inner):
                self_inner._buf = ""
            def write(self_inner, s):
                if s.strip():
                    self._qlog(s.rstrip(), "info")
                return len(s)
            def flush(self_inner):
                pass

        redirector = _Redirector()
        old_stdout  = sys.stdout
        sys.stdout  = redirector

        try:
            run_pipeline(
                patterns_config=cfg["patterns_config"],
                pattern_key=cfg["pattern_key"],
                files_directory=cfg["files_directory"],
                file_pattern=cfg["file_pattern"],
                output_csv=cfg["output_csv"],
                event_keyword=cfg["event_keyword"],
            )

            # Check outputs
            csv_path   = cfg["output_csv"]
            excel_path = csv_path.with_suffix(".xlsx")

            if csv_path.exists():
                self._qlog(f"✔  CSV  → {csv_path}", "success")
            if excel_path.exists():
                self._qlog(f"✔  XLSX → {excel_path}", "success")

            self._qlog("Pipeline completed successfully.", "success")
            self.after(0, lambda: self._set_status("Done", PAL["success"]))

        except Exception as exc:
            self._qlog(f"✘  Error: {exc}", "error")
            import traceback
            for line in traceback.format_exc().splitlines():
                self._qlog(line, "error")
            self.after(0, lambda: self._set_status("Error", PAL["error"]))

        finally:
            sys.stdout = old_stdout
            self.after(0, self._pipeline_done)

    def _pipeline_done(self):
        self._running = False
        self._progress.stop()
        self._run_btn.config(state="normal", text="▶  Run Pipeline")

    def _set_status(self, text: str, colour: str):
        self._status_label.config(text=text, fg=colour)
        self._status_dot.config(fg=colour)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from datetime import datetime   # noqa: F811 (needed for timestamp in _log)
    app = LogParserApp()
    app.mainloop()