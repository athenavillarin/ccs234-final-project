# Discovery tab: local ip, gateway, network range and a table of active devices
from datetime import datetime

import customtkinter as ctk

from core import discovery
from gui.tabs.base_tab import BaseTab
from gui.widgets import make_table
from gui.worker import run_in_background
from services import db

# (column key, heading text, width in pixels) for the device table
COLUMNS = (
    ("ip", "IP Address", 130),
    ("hostname", "Hostname", 220),
    ("mac", "MAC Address", 150),
    ("vendor", "Vendor", 240),
    ("status", "Status", 70),
)

# (card key, label) for the summary cards above the table
CARDS = (
    ("local_ip", "Local IP"),
    ("gateway", "Default Gateway"),
    ("network", "Network Range"),
    ("count", "Active Devices"),
)


# finds the local network details and scans it for active devices
class DiscoveryTab(BaseTab):
    title = "Discovery"
    description = "Local IP, network range and active devices"

    # builds the cards, scan controls and device table, then loads network info
    def build(self):
        self.local_ip = None
        self.network = None
        self.scanning = False
        self.build_cards()
        self.build_controls()
        self.build_table()
        self.load_network_info()

    # row of summary cards: local ip, gateway, range and device count
    def build_cards(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16)
        self.cards = {}
        for index, (key, label) in enumerate(CARDS):
            card = ctk.CTkFrame(row)
            card.pack(side="left", fill="x", expand=True, padx=(0 if index == 0 else 8, 0))
            ctk.CTkLabel(card, text=label, text_color="gray", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=12, pady=(8, 0))
            value = ctk.CTkLabel(card, text="...", font=ctk.CTkFont(size=18, weight="bold"))
            value.pack(anchor="w", padx=12)
            detail = ctk.CTkLabel(card, text="", text_color="gray", font=ctk.CTkFont(size=11))
            detail.pack(anchor="w", padx=12, pady=(0, 8))
            self.cards[key] = (value, detail)

    # scan button, progress bar and progress message
    def build_controls(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)
        self.scan_button = ctk.CTkButton(row, text="Scan Network", width=140, command=self.start_scan)
        self.scan_button.pack(side="left")
        self.progress = ctk.CTkProgressBar(row)
        self.progress.set(0)
        self.progress.pack(side="left", fill="x", expand=True, padx=12)
        self.progress_label = ctk.CTkLabel(row, text="Press Scan Network to find devices", text_color="gray", width=280, anchor="w")
        self.progress_label.pack(side="left")

    # table of devices found by the latest scan
    def build_table(self):
        frame, self.table = make_table(self, COLUMNS)
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    # sets the big value and small detail text of one card
    def set_card(self, key, value, detail=""):
        value_label, detail_label = self.cards[key]
        value_label.configure(text=value)
        detail_label.configure(text=detail)

    # looks up local ip, gateway and range in the background (scapy import is slow)
    def load_network_info(self):
        run_in_background(self, discovery.get_network_info, on_done=self.show_network_info, on_error=self.show_error)

    # fills the cards with the detected network details
    def show_network_info(self, info):
        self.local_ip = info["local_ip"]
        self.network = info["network"]
        self.set_card("local_ip", info["local_ip"], info["hostname"])
        self.set_card("gateway", info["gateway"] or "Unknown", "Router" if info["gateway"] else "")
        usable_hosts = max(self.network.num_addresses - 2, 1)
        self.set_card("network", str(self.network), f"Mask {self.network.netmask} · {usable_hosts} hosts")
        self.set_card("count", "-", "Not scanned yet")

    # starts a scan in a background thread so the window stays responsive
    def start_scan(self):
        if self.scanning:
            return
        self.scanning = True
        self.scan_button.configure(state="disabled", text="Scanning...")
        self.progress.set(0)
        self.app.set_status("Scanning network...")
        run_in_background(self, discovery.scan_network, self.network, self.report_progress,
                          on_done=self.show_devices, on_error=self.show_error)

    # called from the worker thread; hands the update to the gui thread
    def report_progress(self, fraction, message):
        self.after(0, self.show_progress, fraction, message)

    # updates the progress bar and message
    def show_progress(self, fraction, message):
        self.progress.set(fraction)
        self.progress_label.configure(text=message)

    # fills the table with the scan results and shares them with the other tabs
    def show_devices(self, devices):
        self.finish_scan()
        self.table.delete(*self.table.get_children())
        for device in devices:
            hostname = device["hostname"] or "-"
            if device["ip"] == self.local_ip:
                hostname += " (this device)"
            self.table.insert("", "end", values=(device["ip"], hostname, device["mac"] or "-",
                                                 device["vendor"] or "-", device["status"].upper()))
        self.set_card("count", str(len(devices)), "Last scan " + datetime.now().strftime("%I:%M %p"))
        self.app.update_devices(devices)
        self.app.set_status(f"Discovery finished: {len(devices)} active devices")
        network = str(self.network) if self.network else ""
        run_in_background(self, db.record_scan, devices, network,
                          on_done=self.show_saved_scan, on_error=self.show_save_error)

    # tells the other tabs (history) that a new scan was stored
    def show_saved_scan(self, new_devices):
        self.app.broadcast("on_scan_saved")

    # a failed save should not hide the scan results, so only the status bar changes
    def show_save_error(self, error):
        self.app.set_status(f"Scan finished, but saving to history failed: {error}")

    # shows a failed lookup or scan without crashing the app
    def show_error(self, error):
        self.finish_scan()
        self.progress_label.configure(text=f"Error: {error}")
        self.app.set_status("Discovery failed")

    # re-enables the scan button after a scan ends
    def finish_scan(self):
        self.scanning = False
        self.scan_button.configure(state="normal", text="Scan Network")
