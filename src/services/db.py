# sqlite storage, scan history and optional cloud sync
import sqlite3
from contextlib import closing
from pathlib import Path

from utils import config
from utils.device import now_iso

# older scans beyond this count are deleted after each save
MAX_SCANS = 100

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
def save_scan(devices, network=""):
    scanned_at = now_iso()
    # closing() closes the connection; the inner "with connection" commits,
    # or rolls everything back if any insert fails
    with closing(connect()) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO scans (scanned_at, network, device_count) VALUES (?, ?, ?)",
            (scanned_at, str(network), len(devices)))
        scan_id = cursor.lastrowid
        connection.executemany(
            "INSERT INTO scan_devices (scan_id, ip, hostname, mac, vendor, status, avg_latency, max_latency, packet_loss)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(scan_id, device["ip"], device.get("hostname", ""), device.get("mac", ""), device.get("vendor", ""),
              device.get("status", ""), device.get("avg_latency"), device.get("max_latency"), device.get("packet_loss"))
             for device in devices])
        # insert macs seen for the first time, refresh the rest
        connection.executemany(
            "INSERT INTO known_devices (mac, first_seen, last_seen, last_ip, hostname, vendor) VALUES (?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(mac) DO UPDATE SET last_seen = excluded.last_seen, last_ip = excluded.last_ip,"
            " hostname = CASE WHEN excluded.hostname != '' THEN excluded.hostname ELSE known_devices.hostname END,"
            " vendor = excluded.vendor",
            [(device["mac"], scanned_at, scanned_at, device["ip"], device.get("hostname", ""), device.get("vendor", ""))
             for device in devices if device.get("mac")])
        # keep only the newest scans; their device rows go with them (on delete cascade)
        connection.execute(
            "DELETE FROM scans WHERE id NOT IN (SELECT id FROM scans ORDER BY id DESC LIMIT ?)", (MAX_SCANS,))
    return scan_id


# returns past scans, newest first
def get_history(limit=20):
    with closing(connect()) as connection:
        rows = connection.execute(
            "SELECT id, scanned_at, network, device_count FROM scans ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in rows]


# returns the devices saved with one scan, in the order they were found
def get_scan_devices(scan_id):
    with closing(connect()) as connection:
        rows = connection.execute(
            "SELECT ip, hostname, mac, vendor, status, avg_latency, max_latency, packet_loss"
            " FROM scan_devices WHERE scan_id = ? ORDER BY rowid", (scan_id,))
        return [dict(row) for row in rows]


# returns devices in the latest scan that were never seen before
# must run before save_scan, which adds every mac in the scan to known_devices
def find_new_devices(devices):
    with closing(connect()) as connection:
        known = {row["mac"] for row in connection.execute("SELECT mac FROM known_devices")}
    # the very first scan is the baseline, so nothing counts as new yet
    if not known:
        return []
    # devices are matched by mac because ips change when dhcp leases renew
    return [device for device in devices if device.get("mac") and device["mac"] not in known]


# checks a finished scan for new devices, saves it, and returns the new devices
def record_scan(devices, network=""):
    new_devices = find_new_devices(devices)
    save_scan(devices, network)
    return new_devices
