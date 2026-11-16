# shared colors and widgets used by several tabs
from tkinter import ttk

import customtkinter as ctk

TABLE_STYLE = "Table.Treeview"

# colors are (light mode, dark mode) pairs that customtkinter switches automatically
PAGE_BG = ("#F5F7FA", "#1E1F22")
CARD_BG = ("#FFFFFF", "#2B2B2B")
CARD_BORDER = ("#E2E8F0", "#3A3B3E")
SIDEBAR_BG = ("#E9EDF2", "#25262A")
# secondary text, darker than "gray" so it stays readable on light backgrounds
MUTED_TEXT = ("#4D5359", "#A8ADB3")
# warning text, e.g. when the scan had to fall back to the limited ping sweep
WARNING_TEXT = ("#B45309", "#F5B041")


# green for highlighted rows, darker in light mode so it reads on a white table
def highlight_green():
    return "#5BD69A" if ctk.get_appearance_mode() == "Dark" else "#1A7F4B"


# white rounded frame with a thin border, used to group related content
def make_card(parent, **kwargs):
    return ctk.CTkFrame(parent, fg_color=CARD_BG, border_width=1, border_color=CARD_BORDER,
                        corner_radius=8, **kwargs)


# ttk styles are shared by the whole app, so they only need to be set up once
tables_styled = False


# colors ttk tables to match the light or dark customtkinter theme
def style_tables(widget):
    global tables_styled
    if tables_styled:
        return
    tables_styled = True
    dark = ctk.get_appearance_mode() == "Dark"
    background, text, heading = ("#2b2b2b", "#e6e6e6", "#353535") if dark else ("#ffffff", "#1a1a1a", "#eef1f5")
    style = ttk.Style(widget)
    # the default windows theme ignores custom colors, "clam" respects them
    style.theme_use("clam")
    style.configure(TABLE_STYLE, background=background, fieldbackground=background,
                    foreground=text, rowheight=28, borderwidth=0, font=("Segoe UI", 10))
    style.configure(f"{TABLE_STYLE}.Heading", background=heading, foreground=text,
                    relief="flat", font=("Segoe UI", 10, "bold"))
    style.map(TABLE_STYLE, background=[("selected", "#1f6aa5")], foreground=[("selected", "#ffffff")])
    style.map(f"{TABLE_STYLE}.Heading", background=[("active", heading)])


# builds a table with a scrollbar inside a card; columns are (key, heading, width)
# returns (frame, table) so the caller decides where the frame is placed
def make_table(parent, columns, height=10):
    style_tables(parent)
    frame = make_card(parent)
    # ttk treeview is used because customtkinter has no table widget
    table = ttk.Treeview(frame, columns=[key for key, _, _ in columns], show="headings",
                         style=TABLE_STYLE, height=height)
    for key, heading, width in columns:
        table.heading(key, text=heading, anchor="w")
        table.column(key, width=width, minwidth=60, anchor="w")
    scrollbar = ctk.CTkScrollbar(frame, command=table.yview)
    table.configure(yscrollcommand=scrollbar.set)
    table.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
    scrollbar.pack(side="right", fill="y", pady=8)
    return frame, table


# centered message drawn over an empty table, e.g. "No devices yet"
# call .place(relx=0.5, rely=0.5, anchor="center") to show it and .place_forget() to hide it
def make_empty_state(table_frame, text):
    return ctk.CTkLabel(table_frame, text=text, text_color=MUTED_TEXT, fg_color=CARD_BG,
                        font=ctk.CTkFont(size=13))
