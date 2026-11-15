# port scanner with risk notes
# owner: person 3


# scans the given ports on a host and returns the list of open ports
def scan_ports(ip, ports=None, timeout=0.5):
    raise NotImplementedError


# returns a short risk note for an open port, e.g. telnet is unencrypted
def risk_note(port):
    raise NotImplementedError
