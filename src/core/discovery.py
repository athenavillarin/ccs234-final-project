# network discovery: local ip, network range, active devices, hostname, mac vendor
import ipaddress
import platform
import re
import socket
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import config
from utils.device import new_device

IS_WINDOWS = platform.system() == "Windows"

# stops a console window from flashing for every ping when run from the gui on windows
NO_WINDOW = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0

# auto-detected ranges bigger than this are narrowed so a scan stays a few seconds long
SMALLEST_AUTO_PREFIX = 24

# matches "ip ... mac" pairs in `arp -a` output on windows (aa-bb-..) and linux/mac (aa:bb:..)
ARP_LINE = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})\D+?([0-9a-fA-F]{2}(?:[:-][0-9a-fA-F]{2}){5})")

BROADCAST_MAC = "ff:ff:ff:ff:ff:ff"


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


# converts any mac format to lowercase colon form, e.g. aa:bb:cc:dd:ee:ff
def normalize_mac(mac):
    return mac.strip().lower().replace("-", ":")


# returns this machine's mac address on the lan interface
def get_own_mac(local_ip):
    try:
        from scapy.all import conf, get_if_hwaddr
        return normalize_mac(get_if_hwaddr(conf.route.route(local_ip)[0]))
    except Exception:
        # uuid.getnode() returns the mac of one network card as a 48-bit number
        node = uuid.getnode()
        return ":".join(f"{(node >> shift) & 0xFF:02x}" for shift in range(40, -8, -8))


# layer 2 scan: broadcasts an arp "who-has" for every ip and collects the replies
# needs npcap on windows; raises if raw packet access is not available
def arp_scan(network):
    from scapy.all import ARP, Ether, conf, srp

    conf.verb = 0
    # send on the interface that routes to this network
    iface = conf.route.route(str(network.network_address + 1))[0]
    request = Ether(dst=BROADCAST_MAC) / ARP(pdst=str(network))
    # retry=2 resends to silent ips twice, since phones on wi-fi often miss the first request
    answered, _unanswered = srp(request, iface=iface, timeout=2, retry=2)
    # psrc is the ip that replied, hwsrc is its mac address
    return {reply.psrc: normalize_mac(reply.hwsrc) for _sent, reply in answered}


# sends one icmp echo request using the os ping command, True if the host replied
def ping_once(ip):
    timeout_ms = config.PING_TIMEOUT_MS
    if IS_WINDOWS:
        command = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    else:
        command = ["ping", "-c", "1", "-W", str(max(1, timeout_ms // 1000)), ip]
    try:
        result = subprocess.run(command, capture_output=True, text=True, errors="replace",
                                timeout=timeout_ms / 1000 + 2, creationflags=NO_WINDOW)
    except (subprocess.TimeoutExpired, OSError):
        return False
    # windows can exit with 0 on "destination host unreachable",
    # so a real echo reply must also contain a ttl value
    return result.returncode == 0 and "ttl=" in result.stdout.lower()


# reads the os arp cache and returns {ip: mac}
def read_arp_table():
    try:
        output = subprocess.run(["arp", "-a"], capture_output=True, text=True, errors="replace",
                                timeout=10, creationflags=NO_WINDOW).stdout
    except (subprocess.TimeoutExpired, OSError):
        return {}
    return {ip: normalize_mac(mac) for ip, mac in ARP_LINE.findall(output)}


# fallback scan without raw packets: ping every host in parallel, then read the arp cache
def ping_sweep(network, on_progress=None):
    hosts = [str(ip) for ip in network.hosts()]
    alive = set()
    with ThreadPoolExecutor(max_workers=config.SCAN_THREADS) as pool:
        futures = {pool.submit(ping_once, ip): ip for ip in hosts}
        for done, future in enumerate(as_completed(futures), 1):
            if future.result():
                alive.add(futures[future])
            report(on_progress, 0.85 * done / len(hosts), f"Ping sweep: {done}/{len(hosts)} hosts checked")

    # every ping triggers an arp request first, so hosts whose firewall blocks icmp
    # (common on windows pcs and phones) still show up in the arp cache
    found = {ip: "" for ip in alive}
    for ip, mac in read_arp_table().items():
        if mac != BROADCAST_MAC and ipaddress.IPv4Address(ip) in network:
            found[ip] = mac
    return found


# resolves an ip to a hostname, returns "" when it cannot be resolved
def resolve_hostname(ip):
    raise NotImplementedError


# looks up the vendor name for a mac address from the offline oui table
def lookup_vendor(mac):
    raise NotImplementedError


# calls the progress callback if one was given
def report(on_progress, fraction, message):
    if on_progress:
        on_progress(fraction, message)


# scans the range and returns a list of device dicts for responding hosts
# on_progress(fraction, message) is called from the worker thread as the scan advances
def scan_network(network=None, on_progress=None):
    local_ip = get_local_ip()
    network = network or get_network_range(local_ip)

    # try the fast layer 2 arp scan first, fall back to a ping sweep without npcap/admin
    found = {}
    method = "ARP scan"
    try:
        report(on_progress, 0.1, f"ARP scan of {network}...")
        found = arp_scan(network)
    except Exception:
        found = {}
    if not found:
        method = "ping sweep"
        found = ping_sweep(network, on_progress)

    # a host never answers its own arp request, so add this machine manually
    if ipaddress.IPv4Address(local_ip) in network and not found.get(local_ip):
        found[local_ip] = get_own_mac(local_ip)

    devices = [new_device(ip, mac=found[ip], status="up") for ip in sorted(found, key=ipaddress.IPv4Address)]

    report(on_progress, 1.0, f"Found {len(devices)} devices using {method}")
    return devices
