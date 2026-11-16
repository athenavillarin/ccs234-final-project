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

# (column key, heading text, width in pixels) for the devices of the selected scan
DEVICE_COLUMNS = (
    ("ip", "IP Address", 130),
    ("hostname", "Hostname", 220),
    ("mac", "MAC Address", 150),
    ("vendor", "Vendor", 240),
    ("status", "Status", 70),
)


# turns a stored iso timestamp into a readable date, e.g. "Nov 16, 2026  08:05:31 PM"
def format_time(iso_text):
    try:
        return datetime.fromisoformat(iso_text).strftime("%b %d, %Y  %I:%M:%S %p")
    except ValueError:
        return iso_text


# lists past scans from the local database and the devices found in each
class HistoryTab(BaseTab):
    title = "History"
    description = "Past scans stored locally or in the cloud"

    # builds the controls, scan list and device list, then loads saved scans
    def build(self):
        self.build_controls()
        self.build_scan_table()
        self.build_device_table()
        self.load_history()

    # refresh button and a summary of how many scans are saved
    def build_controls(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(row, text="Refresh", width=110, command=self.load_history).pack(side="left")
        self.summary_label = ctk.CTkLabel(row, text="Loading history...", text_color="gray")
        self.summary_label.pack(side="left", padx=12)

    # table of saved scans, newest first; selecting one shows its devices below
    def build_scan_table(self):
        frame, self.scan_table = make_table(self, SCAN_COLUMNS, height=6)
        frame.pack(fill="x", padx=16)
        self.scan_table.configure(selectmode="browse")
        self.scan_table.bind("<<TreeviewSelect>>", self.load_selected_scan)

    # heading and table for the devices of the selected scan
    def build_device_table(self):
        self.detail_label = ctk.CTkLabel(self, text="Select a scan to see its devices",
                                         font=ctk.CTkFont(size=14, weight="bold"))
        self.detail_label.pack(anchor="w", padx=16, pady=(12, 4))
        frame, self.device_table = make_table(self, DEVICE_COLUMNS)
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
            plural = "" if len(scans) == 1 else "s"
            self.summary_label.configure(text=f"{len(scans)} saved scan{plural} (the newest {db.MAX_SCANS} are kept)")
            # show the newest scan's devices right away
            self.scan_table.selection_set(str(scans[0]["id"]))
        else:
            self.summary_label.configure(text="No scans saved yet. Run a scan in the Discovery tab.")
            self.device_table.delete(*self.device_table.get_children())

    # loads the devices of the selected scan in the background
    def load_selected_scan(self, _event=None):
        selection = self.scan_table.selection()
        if not selection:
            return
        scan_id = int(selection[0])
        run_in_background(self, db.get_scan_devices, scan_id,
                          on_done=lambda devices: self.show_scan_devices(scan_id, devices), on_error=self.show_error)

    # fills the device table, unless the user already picked a different scan
    def show_scan_devices(self, scan_id, devices):
        if self.scan_table.selection() != (str(scan_id),):
            return
        self.device_table.delete(*self.device_table.get_children())
        for device in devices:
            self.device_table.insert("", "end", values=(device["ip"], device["hostname"] or "-", device["mac"] or "-",
                                                        device["vendor"] or "-", device["status"].upper()))
        scanned_at = self.scan_table.set(str(scan_id), "scanned_at")
        self.detail_label.configure(text=f"Devices in scan from {scanned_at}")

    # called by the app after the discovery tab stores a scan
    def on_scan_saved(self):
        self.load_history()

    # shows a database error without crashing the app
    def show_error(self, error):
        self.summary_label.configure(text=f"Could not load history: {error}")
