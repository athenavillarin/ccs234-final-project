# shared device record used by every module
from datetime import datetime


# returns the current local time as an iso 8601 string without microseconds
def now_iso():
    return datetime.now().replace(microsecond=0).isoformat()


# builds a device dict in the shared format; unknown fields get safe defaults
def new_device(ip, hostname="", mac="", vendor="", status="down"):
    return {
        "ip": ip,
        "hostname": hostname,
        "mac": mac,
        "vendor": vendor,
        "status": status,
        "avg_latency": None,
        "max_latency": None,
        "packet_loss": 100.0 if status == "down" else 0.0,
        "open_ports": [],
        "last_seen": now_iso() if status == "up" else None,
    }
