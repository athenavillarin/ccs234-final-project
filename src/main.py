# entry point: run with `python src/main.py` from the project root
import customtkinter as ctk

from gui.app import App


# applies the theme and starts the gui event loop
def main():
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
