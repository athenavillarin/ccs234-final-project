# one module per feature tab; TABS sets the order they appear in the window
from gui.tabs.dashboard_tab import DashboardTab
from gui.tabs.discovery_tab import DiscoveryTab
from gui.tabs.connectivity_tab import ConnectivityTab
from gui.tabs.statistics_tab import StatisticsTab
from gui.tabs.monitor_tab import MonitorTab
from gui.tabs.portscan_tab import PortScanTab
from gui.tabs.capture_tab import CaptureTab
from gui.tabs.security_tab import SecurityTab
from gui.tabs.reports_tab import ReportsTab
from gui.tabs.history_tab import HistoryTab

TABS = [
    DashboardTab,
    DiscoveryTab,
    ConnectivityTab,
    StatisticsTab,
    MonitorTab,
    PortScanTab,
    CaptureTab,
    SecurityTab,
    ReportsTab,
    HistoryTab,
]
