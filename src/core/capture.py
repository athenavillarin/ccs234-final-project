# packet capture integration (scapy)


# captures packets for a duration and returns a summary list
def capture_packets(interface=None, duration=10, packet_filter=None):
    raise NotImplementedError


# saves captured packets to a .pcap file that wireshark can open
def save_pcap(packets, path):
    raise NotImplementedError
