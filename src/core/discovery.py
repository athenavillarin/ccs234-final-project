# network discovery: local ip, network range, active devices, hostname, mac vendor


# returns this machine's ip on the active lan interface
def get_local_ip():
    raise NotImplementedError


# returns the network range (ipaddress.IPv4Network) for the local ip
def get_network_range(local_ip=None):
    raise NotImplementedError


# scans the range and returns a list of device dicts for responding hosts
def scan_network(network=None, on_progress=None):
    raise NotImplementedError


# resolves an ip to a hostname, returns "" when it cannot be resolved
def resolve_hostname(ip):
    raise NotImplementedError


# looks up the vendor name for a mac address from the offline oui table
def lookup_vendor(mac):
    raise NotImplementedError
