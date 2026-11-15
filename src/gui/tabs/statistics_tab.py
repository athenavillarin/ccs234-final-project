# Statistics tab
from gui.tabs.base_tab import BaseTab


# placeholder; override build() to add this tab's widgets
class StatisticsTab(BaseTab):
    title = "Statistics"
    description = "Hostname, IP, average and max latency, packet loss per device"
