import scapy.all
import getch
from socket import *
import threading
from struct import unpack

CLIENT_NAME= "CyberPunk2077\n"
source_port = 13117 
FORMAT = 'IBH'
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
    print("connected!")
    return client_tcp_socket



""" The function for the keyboard thread - reads characters from the keyboard and passes them to the server via the socket
    Args: socket - TCP socket that connects the client and the server
    Return: void
                """
def get_from_keyboard(socket):
    while True:
        keyboard_in = getch.getch()
        socket.sendall(keyboard_in.encode())



""" The function for the printing thread - receive messages from server and prints them 
    Args: socket - the TCP socket used to connect the server
    Return: void
                """
def get_msgs_from_server(socket):
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
        tcp_socket.sendall(CLIENT_NAME.encode())

        start_game_msg = tcp_socket.recv(BUFFER_SIZE)
        print(start_game_msg.decode())
        
    except error as err_msg:
        tcp_socket.close()
        print("socket error: " + err_msg)
        return None
        
    get_from_keyboard_thread = threading.Thread(target=get_from_keyboard, args=(tcp_socket,))
    get_msgs_from_server_thread = threading.Thread(target=get_msgs_from_server, args=(tcp_socket,))
        
    get_from_keyboard_thread.start()
    get_msgs_from_server_thread.start()

    get_from_keyboard_thread.join()
    get_msgs_from_server_thread.join()

    print("Server disconnected, listening for offer requests...")
    tcp_socket.close()

if __name__ == "__main__":
    client_states()