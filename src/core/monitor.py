# real-time monitoring loop that pings devices on an interval


# runs periodic pings in a background thread and reports results via callback
class Monitor:
    # stores the devices, interval in seconds and result callback
    def __init__(self, devices, interval=5, on_update=None):
        self.devices = devices
        self.interval = interval
        self.on_update = on_update

    # starts the monitoring thread
    def start(self):
        raise NotImplementedError

    # signals the monitoring thread to stop
    def stop(self):
        raise NotImplementedError
