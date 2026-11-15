# main application window: tab view plus status bar
import customtkinter as ctk

from gui.tabs import TABS
from utils.system import is_admin


# top-level window that hosts every feature tab and shared scan state
class App(ctk.CTk):
    # sets up the window, shared state, tabs and status bar
    def __init__(self):
        super().__init__()
        self.title("Network Monitoring and Performance Analysis System")
        self.geometry("1100x700")
        self.minsize(900, 600)

        # latest device list shared between tabs (shared device dict format)
        self.devices = []
        self.tabs = {}

        self.build_tabs()
        self.build_status_bar()

    # creates one tab per entry in TABS
    def build_tabs(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        for tab_class in TABS:
            frame = self.tabview.add(tab_class.title)
            tab = tab_class(frame, self)
            tab.pack(fill="both", expand=True)
            self.tabs[tab_class.title] = tab

    # bottom bar showing status messages and whether admin rights are available
    def build_status_bar(self):
        bar = ctk.CTkFrame(self, height=28)
        bar.pack(fill="x", padx=10, pady=10)
        self.status_label = ctk.CTkLabel(bar, text="Ready")
        self.status_label.pack(side="left", padx=10)
        admin_text = "Admin: yes" if is_admin() else "Admin: no (limited scan mode)"
        ctk.CTkLabel(bar, text=admin_text, text_color="gray").pack(side="right", padx=10)

    # updates the status bar message; safe to call from the gui thread only
    def set_status(self, text):
        self.status_label.configure(text=text)
