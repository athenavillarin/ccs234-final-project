# os-level checks shared across modules
import ctypes
import os
import platform


# returns True when the app runs with admin/root rights
def is_admin():
    try:
        # windows exposes this through shell32
        if platform.system() == "Windows":
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        # unix-like systems use effective user id 0 for root
        return os.geteuid() == 0
    except (AttributeError, OSError):
        return False
