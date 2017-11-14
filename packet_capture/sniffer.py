# coding=utf-8
import socket
import struct
from scapy.all import ETH_P_IP
from scapy.all import MTU
from collections import defaultdict


# https://github.com/bisrael8191/tcp-fragmentation
# http://wp.me/pDfjR-rQ
# pip install scapy-python3


class IPHeader(object):
    """ IP Header block
        RFC 791
        http://en.wikipedia.org/wiki/IPv4#Header

        IP Header
        0                   1                   2                   3
         1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |Version|  IHL  |Type of Service|          Total Length         |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |         Identification        |Flags|      Fragment Offset    |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |  Time to Live |    Protocol   |         Header Checksum       |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                       Source Address                          |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                    Destination Address                        |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                    Options                    |    Padding    |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Version : 4 is ipv4 and 6 is ipv6
        IHL: IP Header Length, represent how many 32 bit words(4bytes)
            the maximum length is 15 words (15×32 bits) = 60 bytes.
        Type of Service: if not zero first 6 bit define special protocol like VoIP,
            last 2 bit for ECN.
        Total Length: total IP datagram length in bytes.
        Flags:
            bit 0: Reserved; must be zero
            bit 1: Don't Fragment (DF)
            bit 2: More Fragments (MF)
        Fragment Offset: a maximum offset of (2^13 – 1) × 8 = 65,528 bytes
        Time To Live (TTL): how many hops before router drop packets,
            minus 1 when through a router
        Protocol: 1 ICMP, 2 IGMP, 6 TCP, 17 UDP, 41 ENCAP, 89 OSPF, 132 SCTP
        Options: (if IHL > 5)
    """

    IP_HEADER_FMT = struct.Struct('!BBHHHBBH4s4s')

    def __init__(self, ip_frame):
        self.ip_frame = ip_frame

        self.version = 4
        self.header_length = 5  # 5*4 20bytes
        self.type_of_service = 0
        self.total_length = 0
        self.identification = 0
        self.flags = 0
        self.fragment_offset = 0
        self.ttl = 0
        self.protocol = 0
        self.checksum = 0
        self.src = ""
        self.dst = ""
        self.options = []

        self._decode()

    def _decode(self):
        header = self.IP_HEADER_FMT.unpack(self.ip_frame[:self.IP_HEADER_FMT.size])

        self.version = header[0] >> 4
        self.header_length = header[0] & 0xF
        self.type_of_service = header[1]
        self.total_length = header[2]
        self.identification = header[3]
        self.flags = header[4] >> 3
        self.fragment_offset = header[4] & 0xF
        self.ttl = header[5]

        self.protocol = header[6]

        self.checksum = header[7]
        self.src = socket.inet_ntoa(str(header[8]))
        self.dst = socket.inet_ntoa(str(header[9]))

        # Decode additional options (header length is greater than 5)
        if self.header_length > 5:
            num_options = self.header_length - 5
            num_options_bytes = num_options * 4
            self.options = struct.unpack(
                "!%dL" % num_options,
                self.ip_frame[self.IP_HEADER_FMT.size:self.IP_HEADER_FMT.size + num_options_bytes])


class TCPHeader(object):
    """ TDP Header block
        RFC 793
        http://en.wikipedia.org/wiki/Transmission_Control_Protocol#TCP_segment_structure


        0                   1                   2                   3
        1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |          Source Port          |       Destination Port        |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |                        Sequence Number                        |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |                    Acknowledgment Number                      |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |  Data |           |U|A|P|R|S|F|                               |
       | Offset| Reserved  |R|C|S|S|Y|I|            Window             |
       |       |           |G|K|H|T|N|N|                               |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |           Checksum            |         Urgent Pointer        |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |                    Options                    |    Padding    |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |                             data                              |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """

    TCP_HEADER_FMT = struct.Struct('!HHLLBBHHH')

    # Maximum sequence number (numbers rollover back to zero when they reach this point)
    MAX_SEQUENCE = 4294967296

    def __init__(self, ip_frame, ip_header_size):
        self.ip_frame = ip_frame
        self.ip_header_size = ip_header_size

        self.sport = 0
        self.dport = 0
        self.seq = 0
        self.ack = 0
        self.data_offset = 0
        self.reserved = 0

        # Flags
        self.tcp_fin = 0
        self.tcp_syn = 0
        self.tcp_rst = 0
        self.tcp_psh = 0
        self.tcp_ack = 0
        self.tcp_urg = 0
        self.tcp_ece = 0
        self.tcp_cwr = 0

        self.window = 0
        self.checksum = 0
        self.urgent_pointer = 0
        self.options = []

        self._decode()

    def _decode(self):
        header = self.TCP_HEADER_FMT.unpack(
            self.ip_frame[self.ip_header_size:self.ip_header_size + self.TCP_HEADER_FMT.size])
        self.sport = header[0]
        self.dport = header[1]
        self.seq = header[2]
        self.ack = header[3]
        self.data_offset = header[4] >> 4
        self.reserved = header[4] & 0xF

        # Parse out each flag bit
        def is_bit_set(field, offset):
            return 1 if ((field & (1 << offset)) > 0) else 0

        self.tcp_fin = is_bit_set(header[5], 0)
        self.tcp_syn = is_bit_set(header[5], 1)
        self.tcp_rst = is_bit_set(header[5], 2)
        self.tcp_psh = is_bit_set(header[5], 3)
        self.tcp_ack = is_bit_set(header[5], 4)
        self.tcp_urg = is_bit_set(header[5], 5)
        self.tcp_ece = is_bit_set(header[5], 6)
        self.tcp_cwr = is_bit_set(header[5], 7)

        self.window = socket.ntohs(header[6])
        self.checksum = header[7]
        self.urgent_pointer = header[8]

        # Decode additional options (data offset is greater than 5)
        if self.data_offset > 5:
            num_options = self.data_offset - 5
            num_options_bytes = num_options * 4
            header = self.ip_header_size + self.TCP_HEADER_FMT.size
            self.options = struct.unpack(
                "!%dL" % num_options,
                self.ip_frame[header:header + num_options_bytes])


class PacketDecoder(object):
    def __init__(self, ip_frame):
        self.ip_frame = ip_frame
        self.layer = defaultdict(lambda: None)
        self._decode()

    def _decode(self):
        try:
            ip = IPHeader(self.ip_frame)
            self.layer[socket.IPPROTO_IP] = ip

            payload_start = ip.header_length * 4

            if ip.protocol == socket.IPPROTO_TCP:
                tcp = TCPHeader(self.ip_frame, ip.header_length * 4)
                self.layer[socket.IPPROTO_TCP] = tcp
                payload_start += tcp.data_offset * 4
            else:
                print("Unsupported IP protocol: %s" % ip.protocol)

        except Exception as e:
            raise ValueError("Failed to decode packet: %s" % e)


class IPSniffer(object):
    def __init__(self, interface_name, on_ip_incoming, on_ip_outgoing):

        self.interface_name = interface_name
        self.on_ip_incoming = on_ip_incoming
        self.on_ip_outgoing = on_ip_outgoing

        # The raw in (listen) socket is a L2 raw socket that listens
        # for all packets going through a specific interface.
        # SOL_SOCKET: SO_LINGER, SO_RCVBUF, SO_SNDBUF, TCP_NODELAY
        # SO_LINGER 用来设置当套接字关闭的时候，不需要进行TIME_WAIT，直接关闭
        # 这个选项虽然是通用的套接字选项，不过只对tcp有用
        # SO_RCVBUF，SO_SNDBUF 用来设置接收缓冲区，和发送缓冲区
        # SO_SNDBUF 小于 MSS，内核会调整为 2MSS
        # TCP_NODELAY  禁止 nagle 算法
        self.sock = socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_IP))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 ** 30)
        self.sock.bind((self.interface_name, ETH_P_IP))

    def __process_ipframe(self, pkt_type, payload):
        if pkt_type == socket.PACKET_OUTGOING:
            if self.on_ip_outgoing is not None:
                self.on_ip_outgoing(payload)

        else:
            if self.on_ip_incoming is not None:
                self.on_ip_incoming(payload)

    def recv(self):
        while True:

            pkt, sa_ll = self.sock.recvfrom(MTU)

            if type == socket.PACKET_OUTGOING and self.on_ip_outgoing is None:
                continue
            elif self.on_ip_outgoing is None:
                continue

            if len(pkt) <= 0:
                break

            eth_header = struct.unpack("!6s6sH", pkt[0:14])

            dummy_eth_protocol = socket.ntohs(eth_header[2])

            if eth_header[2] != ETH_P_IP:
                continue

            ip_header = pkt[14:34]
            payload = pkt[14:]

            self.__process_ipframe(sa_ll[2], payload)


# run code
def incoming_callback(frame):
    decoder = PacketDecoder(frame)
    ip = decoder.layer[socket.IPPROTO_IP]
    tcp = decoder.layer[socket.IPPROTO_TCP]

    print("incoming src=%s:%d, dst=%s:%d, packet len= %d" %
          (ip.src, tcp.sport, ip.dst, tcp.dport, ip.total_length))


def outgoing_callback(frame):
    decoder = PacketDecoder(frame)
    ip = decoder.layer[socket.IPPROTO_IP]
    tcp = decoder.layer[socket.IPPROTO_TCP]

    print("outgoing src=%s:%d, dst=%s:%d, packet len= %d" %
          (ip.src, tcp.sport, ip.dst, tcp.dport, ip.total_length))


ip_sniff = IPSniffer('eth0', incoming_callback, outgoing_callback)
ip_sniff.recv()
