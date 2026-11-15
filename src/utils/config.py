# loads settings from .env so no ips or credentials are hardcoded
import os
from pathlib import Path

from dotenv import load_dotenv

# project root is two levels above this file (src/utils -> project)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# read .env once at import; missing file is fine, defaults below apply
load_dotenv(PROJECT_ROOT / ".env")


# returns a string setting, or the default when unset or blank
def get_str(key, default=""):
    value = os.getenv(key, "").strip()
    return value if value else default


# returns an integer setting, falling back to the default on bad input
def get_int(key, default):
    try:
        return int(get_str(key, str(default)))
    except ValueError:
        return default


# network scan settings; an empty scan range means auto-detect
SCAN_RANGE = get_str("SCAN_RANGE")
PING_COUNT = get_int("PING_COUNT", 4)
PING_TIMEOUT_MS = get_int("PING_TIMEOUT_MS", 1000)
SCAN_THREADS = get_int("SCAN_THREADS", 64)

# local database location, relative paths resolve from the project root
DB_PATH = PROJECT_ROOT / get_str("DB_PATH", "data/history.db")

# smtp settings for email notifications
SMTP_HOST = get_str("SMTP_HOST")
SMTP_PORT = get_int("SMTP_PORT", 587)
SMTP_USER = get_str("SMTP_USER")
SMTP_PASSWORD = get_str("SMTP_PASSWORD")
ALERT_EMAIL_TO = get_str("ALERT_EMAIL_TO")

# optional cloud database credentials
CLOUD_DB_URL = get_str("CLOUD_DB_URL")
CLOUD_DB_KEY = get_str("CLOUD_DB_KEY")
