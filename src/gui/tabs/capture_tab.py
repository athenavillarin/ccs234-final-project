# Capture tab
from gui.tabs.base_tab import BaseTab


# placeholder; override build() to add this tab's widgets
class CaptureTab(BaseTab):
    title = "Capture"
    description = "Packet capture with Wireshark-compatible export"
