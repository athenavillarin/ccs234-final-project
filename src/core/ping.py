# connectivity testing: ping, response time, packet loss
# owner: person 2


# pings one host and returns {"avg_latency", "max_latency", "packet_loss", "status"}
def ping_host(ip, count=4, timeout_ms=1000):
    raise NotImplementedError


# pings every device in the list and updates each dict in place
def ping_devices(devices, on_progress=None):
    raise NotImplementedError
