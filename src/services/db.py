# sqlite storage, scan history and optional cloud sync
# owner: person 1


# creates the database file and tables if they do not exist
def init_db(path=None):
    raise NotImplementedError


# saves one scan (timestamp and device list) and returns its id
def save_scan(devices):
    raise NotImplementedError


# returns past scans, newest first
def get_history(limit=20):
    raise NotImplementedError


# returns devices in the latest scan that were never seen before
def find_new_devices(devices):
    raise NotImplementedError
