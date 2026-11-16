# network discovery: local ip, network range, active devices, hostname, mac vendor
import ipaddress
import socket

from utils import config

# auto-detected ranges bigger than this are narrowed so a scan stays a few seconds long
SMALLEST_AUTO_PREFIX = 24


# returns this machine's ip on the active lan interface
def get_local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # connecting a udp socket sends no packets; it only makes the os choose
        # the outgoing interface, and that interface's address is our lan ip
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        # no default route (offline lan), fall back to the hostname lookup
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"
    finally:
        sock.close()


# returns the default gateway (router) ip, or "" when it cannot be found
def get_gateway():
    try:
        from scapy.all import conf
        gateway = conf.route.route("0.0.0.0")[2]
        return "" if gateway == "0.0.0.0" else gateway
    except Exception:
        return ""


# reads the subnet prefix length of the local ip from the os routing table
def find_prefix_length(local_ip):
    try:
        from scapy.all import conf
        ip_value = int(ipaddress.IPv4Address(local_ip))
        best = None
        # each route is (network, netmask, gateway, interface, source ip, metric)
        for net, mask, _gateway, _iface, source, _metric in conf.route.routes:
            # skip the default route (mask 0) and single-host routes (mask /32)
            if source != local_ip or mask in (0, 0xFFFFFFFF):
                continue
            # the route must actually contain our ip (this skips multicast routes)
            if ip_value & mask != net:
                continue
            prefix = bin(mask).count("1")
            best = prefix if best is None else max(best, prefix)
        if best is not None:
            return best
    except Exception:
        pass
    # most home and school lans use a /24 (255.255.255.0) mask
    return 24


# returns the network range (ipaddress.IPv4Network) for the local ip
def get_network_range(local_ip=None):
    # a range set in .env always wins
    if config.SCAN_RANGE:
        return ipaddress.IPv4Network(config.SCAN_RANGE, strict=False)
    local_ip = local_ip or get_local_ip()
    prefix = max(find_prefix_length(local_ip), SMALLEST_AUTO_PREFIX)
    return ipaddress.IPv4Network(f"{local_ip}/{prefix}", strict=False)


# collects local ip, hostname, gateway and range in one call for the gui
def get_network_info():
    local_ip = get_local_ip()
    return {
        "local_ip": local_ip,
        "hostname": socket.gethostname(),
        "gateway": get_gateway(),
        "network": get_network_range(local_ip),
    }


# scans the range and returns a list of device dicts for responding hosts
def scan_network(network=None, on_progress=None):
    raise NotImplementedError


# resolves an ip to a hostname, returns "" when it cannot be resolved
def resolve_hostname(ip):
    raise NotImplementedError


# looks up the vendor name for a mac address from the offline oui table
def lookup_vendor(mac):
    raise NotImplementedError
