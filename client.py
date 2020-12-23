import scapy.all
from sys import stdin
from socket import *
import threading
from struct import pack, unpack

CLIENT_NAME= "CyberPunk2077"
source_port = 13117 
FORMAT = 'ich'
MAGIC_COOKIE = 0xfeedbeef
OFFER_MSG_TYPE = 0x02
BUFFER_SIZE = 2048



""" The main function for transition between the client's states - first looking for a server, then connecting and after it being in game mode
    Args: no args
    Return: void
                """
def client_states():
    while True:
        server_addr = looking_for_a_server()
        tcp_socket = connecting_to_server(server_addr)
        if tcp_socket == None:
            continue
        game_mode(tcp_socket)



""" The function for the first state- client listening for server offer requests in UDP socket 
    Args: no args
    Return: server's ip address, server's port
                                            """
def looking_for_a_server():
    with socket(AF_INET, SOCK_DGRAM) as client_udp_socket:
        print("Client started, listening for offer requests...")
        client_udp_socket.bind(('', source_port))
        while True:
            message, (server_ip, _) = client_udp_socket.recvfrom(BUFFER_SIZE)
            rcv_cookie, rcv_message_type, server_port = unpack(FORMAT, message)
            if rcv_cookie != MAGIC_COOKIE:
                continue
            if rcv_message_type != OFFER_MSG_TYPE:
                continue
            print("Received offer from " + str(server_ip) + ", attempting to connect...")
            break
        return server_ip, server_port



""" The function for the second state- connect to server 
    Args: serverAddress - (server_ip, server_port) of the server to connect
    Return: tcp_socket for sending and receiving
                                                """
def connecting_to_server(serverAddress):
    client_tcp_socket = socket(AF_INET, SOCK_STREAM)
    try:
        client_tcp_socket.connect(serverAddress)
    except error as err_msg:
        print("Couldn't connect to " + str(serverAddress) + ", error: " + str(err_msg))
        print("Looking for another server...")
        return None
    return client_tcp_socket



""" The function for the keyboard thread - reads characters from the keyboard and passes them to the server via the socket
    Args: socket - TCP socket that connects the client and the server
    Return: void
                """
def get_from_keyboard(socket):
    with socket:
        while True:
            keyboard_in = stdin.read(1)
            socket.sendall(keyboard_in.encode())



""" The function for the printing thread - receive messages from server and prints them 
    Args: socket - the TCP socket used to connect the server
    Return: void
                """
def get_msg_from_server(socket):
    with socket:
        while True:
            new_msg = socket.recv(BUFFER_SIZE)
            if not new_msg:
                break
            print(new_msg.decode())



""" The function for the third state- game mode in which two threads work in same time - one for keyboard input and the second for receiving server's messages
    Args: socket - the TCP socket used to connect the server
    Return: void
                """
def game_mode(tcp_socket):
    try:
        tcp_socket.sendall(bytes(CLIENT_NAME + '\n'))

        start_game_msg = tcp_socket.recv(BUFFER_SIZE)
        print(start_game_msg.decode())
        
    except error as err_msg:
        tcp_socket.close()
        print("socket error: " + err_msg)
        return None
        
    get_from_keyboard_thread = threading.Thread(target=get_from_keyboard, args=(tcp_socket,))
    get_msg_from_server_thread = threading.Thread(target=get_msg_from_server, args=(tcp_socket,))
        
    get_from_keyboard_thread.start()
    get_msg_from_server_thread.start()

    get_from_keyboard_thread.join()
    get_msg_from_server_thread.join()

    print("Server disconnected, listening for offer requests...")
    tcp_socket.close()
