# shared widgets used by several tabs
from tkinter import ttk

import customtkinter as ctk

TABLE_STYLE = "Table.Treeview"

# ttk styles are shared by the whole app, so they only need to be set up once
tables_styled = False


# colors ttk tables to match the light or dark customtkinter theme
def style_tables(widget):
    global tables_styled
    if tables_styled:
        return
    tables_styled = True
    dark = ctk.get_appearance_mode() == "Dark"
    background, text, heading = ("#2b2b2b", "#e6e6e6", "#353535") if dark else ("#ffffff", "#1a1a1a", "#e8e8e8")
    style = ttk.Style(widget)
    # the default windows theme ignores custom colors, "clam" respects them
    style.theme_use("clam")
    style.configure(TABLE_STYLE, background=background, fieldbackground=background,
                    foreground=text, rowheight=28, borderwidth=0, font=("Segoe UI", 10))
    style.configure(f"{TABLE_STYLE}.Heading", background=heading, foreground=text,
                    relief="flat", font=("Segoe UI", 10, "bold"))
    style.map(TABLE_STYLE, background=[("selected", "#1f6aa5")], foreground=[("selected", "#ffffff")])
    style.map(f"{TABLE_STYLE}.Heading", background=[("active", heading)])


# builds a table with a scrollbar inside a frame; columns are (key, heading, width)
# returns (frame, table) so the caller decides where the frame is placed
def make_table(parent, columns, height=10):
    style_tables(parent)
    frame = ctk.CTkFrame(parent)
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
