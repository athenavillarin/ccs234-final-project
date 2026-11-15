# shared base for feature tabs; shows a placeholder until build() is overridden
import customtkinter as ctk


# frame with a header; subclasses set title/description and override build()
class BaseTab(ctk.CTkFrame):
    title = "Tab"
    description = ""

    # creates the header then lets the subclass add its widgets
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.build_header()
        self.build()

    # draws the tab title and short description
    def build_header(self):
        ctk.CTkLabel(self, text=self.title, font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=16, pady=(12, 0))
        ctk.CTkLabel(self, text=self.description, text_color="gray").pack(anchor="w", padx=16, pady=(0, 12))

    # default content until the feature is implemented
    def build(self):
        ctk.CTkLabel(self, text="Coming soon", font=ctk.CTkFont(size=14, slant="italic")).pack(expand=True)
