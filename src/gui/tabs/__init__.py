# one module per feature page; GROUPS sets the sidebar headings and page order
from gui.tabs.dashboard_tab import DashboardTab
from gui.tabs.discovery_tab import DiscoveryTab
from gui.tabs.connectivity_tab import ConnectivityTab
from gui.tabs.portscan_tab import PortScanTab
from gui.tabs.monitor_tab import MonitorTab
from gui.tabs.capture_tab import CaptureTab
from gui.tabs.security_tab import SecurityTab
from gui.tabs.reports_tab import ReportsTab

# (sidebar heading, pages under it); the first page is shown when the app opens
GROUPS = [
    ("Overview", [DashboardTab]),
    ("Network", [DiscoveryTab, ConnectivityTab, PortScanTab]),
    ("Traffic", [MonitorTab, CaptureTab]),
    ("Analysis", [SecurityTab, ReportsTab]),
]
