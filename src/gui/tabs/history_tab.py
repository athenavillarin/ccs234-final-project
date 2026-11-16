# History tab: past scans saved in the local database
from datetime import datetime

import customtkinter as ctk

from gui.tabs.base_tab import BaseTab
from gui.widgets import make_table
from gui.worker import run_in_background
from services import db

# (column key, heading text, width in pixels) for the scan list
SCAN_COLUMNS = (
    ("scanned_at", "Date and Time", 220),
    ("network", "Network", 180),
    ("device_count", "Devices", 90),
)


# turns a stored iso timestamp into a readable date, e.g. "Nov 16, 2026  08:05:31 PM"
def format_time(iso_text):
    try:
        return datetime.fromisoformat(iso_text).strftime("%b %d, %Y  %I:%M:%S %p")
    except ValueError:
        return iso_text


# lists past scans from the local database
class HistoryTab(BaseTab):
    title = "History"
    description = "Past scans stored locally or in the cloud"

    # builds the controls and scan list, then loads saved scans
    def build(self):
        self.build_controls()
        self.build_scan_table()
        self.load_history()

    # refresh button and a summary of how many scans are saved
    def build_controls(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(row, text="Refresh", width=110, command=self.load_history).pack(side="left")
        self.summary_label = ctk.CTkLabel(row, text="Loading history...", text_color="gray")
        self.summary_label.pack(side="left", padx=12)

    # table of saved scans, newest first
    def build_scan_table(self):
        frame, self.scan_table = make_table(self, SCAN_COLUMNS)
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    # reads saved scans in the background so the window stays responsive
    def load_history(self):
        run_in_background(self, db.get_history, db.MAX_SCANS, on_done=self.show_history, on_error=self.show_error)

    # fills the scan list; the scan id is used as the row id
    def show_history(self, scans):
        self.scan_table.delete(*self.scan_table.get_children())
        for scan in scans:
            self.scan_table.insert("", "end", iid=str(scan["id"]),
                                   values=(format_time(scan["scanned_at"]), scan["network"] or "-", scan["device_count"]))
        if scans:
            self.summary_label.configure(text=f"{len(scans)} saved scans (the newest {db.MAX_SCANS} are kept)")
        else:
            self.summary_label.configure(text="No scans saved yet. Run a scan in the Discovery tab.")

    # called by the app after the discovery tab stores a scan
    def on_scan_saved(self):
        self.load_history()

    # shows a database error without crashing the app
    def show_error(self, error):
        self.summary_label.configure(text=f"Could not load history: {error}")
