import scapy.all
from socket import *
from struct import pack

source_port = 13117
udp_client_socket = socket(AF_INET, SOCK_DGRAM)

udp_client_socket.bind(('', source_port))