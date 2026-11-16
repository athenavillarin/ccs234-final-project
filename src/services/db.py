# sqlite storage, scan history and optional cloud sync
import sqlite3
from pathlib import Path

from utils import config

# scans: one row per scan
# scan_devices: the devices found in each scan, removed together with their scan
# known_devices: every mac address ever seen, used to spot new devices
SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scanned_at TEXT NOT NULL,
    network TEXT NOT NULL DEFAULT '',
    device_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS scan_devices (
    scan_id INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    ip TEXT NOT NULL,
    hostname TEXT NOT NULL DEFAULT '',
    mac TEXT NOT NULL DEFAULT '',
    vendor TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT '',
    avg_latency REAL,
    max_latency REAL,
    packet_loss REAL
);
CREATE INDEX IF NOT EXISTS idx_scan_devices_scan ON scan_devices(scan_id);
CREATE TABLE IF NOT EXISTS known_devices (
    mac TEXT PRIMARY KEY,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    last_ip TEXT NOT NULL DEFAULT '',
    hostname TEXT NOT NULL DEFAULT '',
    vendor TEXT NOT NULL DEFAULT ''
);
"""

# database file in use, and whether its tables have been created yet
db_path = config.DB_PATH
db_ready = False


# creates the database file and tables if they do not exist
def init_db(path=None):
    global db_path, db_ready
    if path:
        db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA)
    finally:
        connection.close()
    db_ready = True
    return db_path


# opens a new connection; each call gets its own because sqlite
# connections cannot be shared between the gui thread and scan threads
def connect():
    if not db_ready:
        init_db()
    connection = sqlite3.connect(db_path, timeout=10)
    connection.row_factory = sqlite3.Row
    # sqlite leaves foreign keys off by default, and cascade deletes need them
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# saves one scan (timestamp and device list) and returns its id
def save_scan(devices):
    raise NotImplementedError


# returns past scans, newest first
def get_history(limit=20):
    raise NotImplementedError


# returns devices in the latest scan that were never seen before
def find_new_devices(devices):
    raise NotImplementedError
