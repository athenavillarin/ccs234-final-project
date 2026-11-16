# main application window: sidebar navigation, page area and status bar
import customtkinter as ctk

from gui.tabs import GROUPS
from gui.widgets import CARD_BG, MUTED_TEXT, PAGE_BG, SIDEBAR_BG, WARNING_TEXT, make_card
from utils.system import is_admin

# sidebar button colors (light, dark); the selected page gets a soft blue highlight
NAV_TEXT = ("#1A1A1A", "#E6E6E6")
NAV_HOVER = ("#DCE2EA", "#303136")
NAV_SELECTED = ("#D6E4F5", "#1F6AA5")
NAV_SELECTED_TEXT = ("#0F4C81", "#FFFFFF")


# top-level window that hosts every feature page and shared scan state
class App(ctk.CTk):
    # sets up the window, shared state, sidebar, pages and status bar
    def __init__(self):
        super().__init__()
        self.title("Network Monitoring and Performance Analysis System")
        self.geometry("1150x720")
        self.minsize(950, 600)
        self.configure(fg_color=PAGE_BG)

        # latest device list shared between pages (shared device dict format)
        self.devices = []
        self.tabs = {}
        self.nav_buttons = {}
        self.current_tab = None
        self.admin = is_admin()

        # column 0 is the sidebar, column 1 holds the page above the status bar
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.build_sidebar()
        self.build_pages()
        self.build_status_bar()
        self.show_tab(GROUPS[0][1][0].title)

    # app name, then one heading per group with a button for each page
    def build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color=SIDEBAR_BG)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="ns")
        # keep the fixed width instead of shrinking to the buttons
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sidebar, text="Network Monitor", font=ctk.CTkFont(size=17, weight="bold"),
                     anchor="w").grid(sticky="ew", padx=20, pady=(20, 0))
        ctk.CTkLabel(sidebar, text="Performance Analysis System", text_color=MUTED_TEXT,
                     font=ctk.CTkFont(size=12), anchor="w").grid(sticky="ew", padx=20, pady=(0, 8))

        for group, tab_classes in GROUPS:
            ctk.CTkLabel(sidebar, text=group.upper(), text_color=MUTED_TEXT, anchor="w",
                         font=ctk.CTkFont(size=11, weight="bold")).grid(sticky="ew", padx=20, pady=(14, 2))
            for tab_class in tab_classes:
                title = tab_class.title
                button = ctk.CTkButton(sidebar, text=title, anchor="w", height=34, corner_radius=6,
                                       fg_color="transparent", hover_color=NAV_HOVER, text_color=NAV_TEXT,
                                       font=ctk.CTkFont(size=13), command=lambda t=title: self.show_tab(t))
                button.grid(sticky="ew", padx=12, pady=1)
                self.nav_buttons[title] = button

    # creates every page up front so scans keep running while another page is shown
    def build_pages(self):
        self.page_area = ctk.CTkFrame(self, fg_color="transparent")
        self.page_area.grid(row=0, column=1, sticky="nsew", padx=12, pady=(12, 0))
        for _group, tab_classes in GROUPS:
            for tab_class in tab_classes:
                self.tabs[tab_class.title] = tab_class(self.page_area, self)

    # hides the current page, shows the chosen one and highlights its sidebar button
    def show_tab(self, title):
        if self.current_tab:
            self.tabs[self.current_tab].pack_forget()
            self.nav_buttons[self.current_tab].configure(fg_color="transparent", hover_color=NAV_HOVER,
                                                         text_color=NAV_TEXT)
        self.tabs[title].pack(fill="both", expand=True)
        self.nav_buttons[title].configure(fg_color=NAV_SELECTED, hover_color=NAV_SELECTED,
                                          text_color=NAV_SELECTED_TEXT)
        self.current_tab = title

    # bottom bar: status messages on the left, admin rights and last scan method on the right
    def build_status_bar(self):
        bar = make_card(self, height=34)
        bar.grid(row=1, column=1, sticky="ew", padx=12, pady=12)
        self.status_label = ctk.CTkLabel(bar, text="Ready", fg_color=CARD_BG)
        self.status_label.pack(side="left", padx=12, pady=4)
        self.scan_mode_label = ctk.CTkLabel(bar, text="", text_color=MUTED_TEXT, fg_color=CARD_BG)
        self.scan_mode_label.pack(side="right", padx=12, pady=4)
        self.set_scan_method(None)

    # shows which discovery method the last scan used; the ping sweep is flagged as limited
    def set_scan_method(self, method):
        admin_text = "Admin: yes" if self.admin else "Admin: no"
        if method is None:
            self.scan_mode_label.configure(text=f"{admin_text}  ·  Not scanned yet", text_color=MUTED_TEXT)
        elif method == "ping sweep":
            self.scan_mode_label.configure(
                text=f"{admin_text}  ·  Last scan: ping sweep (limited, run as admin with Npcap for ARP)",
                text_color=WARNING_TEXT)
        else:
            self.scan_mode_label.configure(text=f"{admin_text}  ·  Last scan: {method}", text_color=MUTED_TEXT)

    # stores the latest scan results and passes them to pages that define on_devices_updated
    def update_devices(self, devices):
        self.devices = devices
        self.broadcast("on_devices_updated", devices)

    # calls method_name(*args) on every page that defines it
    def broadcast(self, method_name, *args):
        for tab in self.tabs.values():
            handler = getattr(tab, method_name, None)
            if handler:
                handler(*args)

    # updates the status bar message; safe to call from the gui thread only
    def set_status(self, text):
        self.status_label.configure(text=text)
