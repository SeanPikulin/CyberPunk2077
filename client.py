import scapy.all
from socket import *
from struct import pack, unpack


source_port = 13117
format = 'ich'
MAGIC_COOKIE = 0xfeedbeef
OFFER_MSG_TYPE = 0x02
CLIENT_NAME= "CyberPunk2077"


def client_states():
    while True:
        server_addr = looking_for_a_server()
        tcp_socket = connecting_to_server(server_addr)
        if tcp_socket == None:
            continue
        game_mode(tcp_socket)

def looking_for_a_server():
    with socket(AF_INET, SOCK_DGRAM) as client_udp_socket:
        print("Client started, listening for offer requests...")
        client_udp_socket.bind(('', source_port))
        while True:
            message, (server_ip, _) = client_udp_socket.recvfrom(2048)
            rcv_cookie, rcv_message_type, server_port = unpack(format, message)
            if rcv_cookie != MAGIC_COOKIE:
                continue
            if rcv_message_type != OFFER_MSG_TYPE:
                continue
            print("Received offer from " + str(server_ip) + ", attempting to connect...")
            break
        return server_ip, server_port
        
            

def connecting_to_server(serverAddress):
    client_tcp_socket = socket(AF_INET, SOCK_STREAM)
    try:
        client_tcp_socket.connect(serverAddress)
    except error as err_msg:
        print("Couldn't connect to " + str(serverAddress) + ", error: " + str(err_msg))
        print("Looking for another server...")
        return None
    return client_tcp_socket

def game_mode(tcp_socket):
    try:
        tcp_socket.sendall(bytes(CLIENT_NAME + '\n'))

        start_game_msg = tcp_socket.recv(2048)
        print(start_game_msg.decode())
        
        
    except error as err_msg:
        tcp_socket.close()
        print("socket error: " + err_msg)
