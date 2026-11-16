# Reports page: saved scans and their devices; report export will be added here
from datetime import datetime

import customtkinter as ctk

from gui.tabs.base_tab import BaseTab
from gui.widgets import MUTED_TEXT, make_table
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
class ReportsTab(BaseTab):
    title = "Reports"
    description = "Saved scans and diagnostic reports"

    # builds the controls, scan list and device list, then loads saved scans
    def build(self):
        # counts history loads so an older, slower load cannot overwrite a newer one
        self.load_number = 0
        self.build_controls()
        self.build_scan_table()
        self.build_device_table()
        self.load_history()

    # refresh button and a summary of how many scans are saved
    def build_controls(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(row, text="Refresh", width=110, command=self.load_history).pack(side="left")
        self.summary_label = ctk.CTkLabel(row, text="Loading history...", text_color=MUTED_TEXT)
        self.summary_label.pack(side="left", padx=12)

    # table of saved scans, newest first; selecting one shows its devices below
    def build_scan_table(self):
        frame, self.scan_table = make_table(self, SCAN_COLUMNS, height=6)
        frame.pack(fill="x", padx=16)
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
        self.load_number += 1
        load_number = self.load_number
        run_in_background(self, db.get_history, on_done=lambda scans: self.show_history(load_number, scans),
                          on_error=self.show_error)

    # fills the scan list; the scan id is used as the row id
    def show_history(self, load_number, scans):
        if load_number != self.load_number:
            return
        rows_before = self.scan_table.get_children()
        newest_before = rows_before[0] if rows_before else None
        selected_before = self.scan_table.selection()
        self.scan_table.delete(*rows_before)
        for scan in scans:
            self.scan_table.insert("", "end", iid=str(scan["id"]),
                                   values=(format_time(scan["scanned_at"]), scan["network"] or "-", scan["device_count"]))
        if not scans:
            self.summary_label.configure(text="No scans saved yet. Run a scan in Discovery first.")
            self.clear_details()
            return
        plural = "" if len(scans) == 1 else "s"
        self.summary_label.configure(text=f"{len(scans)} saved scan{plural} (the newest {db.MAX_SCANS} are kept)")
        # stay on a scan the user picked; otherwise follow the newest scan
        picked = selected_before[0] if selected_before and selected_before[0] != newest_before else None
        target = picked if picked and self.scan_table.exists(picked) else str(scans[0]["id"])
        self.scan_table.selection_set(target)
        self.scan_table.see(target)

    # empties the device table and resets its heading
    def clear_details(self):
        self.device_table.delete(*self.device_table.get_children())
        self.detail_label.configure(text="Select a scan to see its devices")

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
        self.clear_details()
