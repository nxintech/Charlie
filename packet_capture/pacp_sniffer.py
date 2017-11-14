import pcap
import socket
import dpkt
from datetime import datetime as dt


def pcap_callback(ts, pkt):
    eth = dpkt.ethernet.Ethernet(pkt)
    if isinstance(eth.data, dpkt.ip.IP):
        ip = eth.data

        if isinstance(ip.data, dpkt.tcp.TCP):
            tcp = ip.data
            print("%s %s:%d -> %s:%d %d" %
                  (dt.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
                   socket.inet_ntoa(ip.src), tcp.sport,
                   socket.inet_ntoa(ip.dst), tcp.dport, len(tcp)))


sniffer = pcap.pcap(name='eth0', promisc=True, immediate=True, timeout_ms=50)

for ts, pkt in sniffer:
    pcap_callback(ts, pkt)
