import struct
import binascii
import socket
import sys

if (sys.version_info > (3, 0)):
    from ipaddress import ip_address as ip_addr
else:
    from ipaddr import IPAddress as ip_addr

def hex_to_ip(convert):
    final_ip = None
    try:
        addr_long = int(str(convert), 16)
        hex(addr_long)
        struct.pack(">L", addr_long)
        final_ip = socket.inet_ntoa(struct.pack(">L", addr_long))
    except Exception as e:
        pass
        print(e)
    if final_ip is not None:
        return final_ip

"""Converts IPv4 Address to hex"""


def ip_to_hex(ip_to_convert):
    return binascii.hexlify(socket.inet_aton(ip_to_convert)).decode(encoding='UTF-8')

def private_check(ip):
    return ip_addr(ip).is_private

def multicast_check(ip):
    return ip_addr(ip).is_multicast

def reserved_check(ip):
    return ip_addr(ip).is_reserved