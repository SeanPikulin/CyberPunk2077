import scapy.all
from socket import *
import threading
from multiprocessing import Process
from struct import unpack
import errno
# import getch
import termios
from tty import setraw
import sys, tty
from termcolor import colored
import select
import os

CLIENT_NAME= "CyberPunk2077\n"
source_port = 13117 
FORMAT = '!IcH'
MAGIC_COOKIE = 0xfeedbeef
OFFER_MSG_TYPE = b'\x02'
BUFFER_SIZE = 2048


""" The main function for transition between the client's states - first looking for a server, then connecting and after it being in game mode
    Args: no args
    Return: void
                """
def client_states():
    print("Client started, listening for offer requests...")
    while True:
        server_addr = looking_for_a_server()
        tcp_socket = connecting_to_server(server_addr)
        if tcp_socket == None:
            continue
        game_mode(tcp_socket)



""" The function for the first state - client listening for server offer requests in UDP socket 
    Args: no args
    Return: server's ip address, server's port
                                            """
def looking_for_a_server():
    with socket(AF_INET, SOCK_DGRAM) as client_udp_socket:
        client_udp_socket.bind(('', source_port))
        client_udp_socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        client_udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        while True:
            message, (server_ip, _) = client_udp_socket.recvfrom(BUFFER_SIZE)
            try:
                rcv_cookie, rcv_message_type, server_port = unpack(FORMAT, message)
            except struct.error as struct_error:
                continue
            if rcv_cookie != MAGIC_COOKIE:
                continue
            if rcv_message_type != OFFER_MSG_TYPE:
                continue
            print("Received offer from " + str(server_ip) + ", attempting to connect...")
            break
        return server_ip, server_port



""" The function for the second state - connect to server 
    Args: serverAddress - (server_ip, server_port) of the server to connect
    Return: tcp_socket for sending and receiving
                                                """
def connecting_to_server(serverAddress):
    client_tcp_socket = socket(AF_INET, SOCK_STREAM)
    try:
        client_tcp_socket.connect(serverAddress)
    except error as err_msg:
        print("Couldn't connect to " + str(serverAddress) + ", error: " + str(err_msg) + "\n")
        print("Looking for another server...\n")
        return None
    print("Connected!\n")
    client_tcp_socket.setblocking(0)
    return client_tcp_socket



""" The function for reading input from stdin
    Args: no args
    Return:  the read char
                                                """
def read_from_stdin():
    try:
        read_char = os.read(0, 1)
    except error as err:
        print("error reading input:" + str(err))
    return read_char



""" The function for the reading from keyboard thread - reads charachters and sends them to the server with the socket
    Args: key - key that was pressed
          tcp_socket - the socket that connects to the server
    Return: False - thrown when the thread stops working
                                                            """
def get_from_keyboard(tcp_socket, fd):
    save_state = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
    except:
        print("Unknown error")
    try:
        while True:
            # key = getch.getch()
            key = read_from_stdin()
            if not key:
                continue
            tcp_socket.sendall(str(key).encode())
    except error as err:
        print("socket error in receiving keyboard input: " + str(err))
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, save_state)
        return False



""" The function for the printing thread - receive messages from server and prints them 
    Args: socket - the TCP socket used to connect the server
    Return: void
                """
def get_msgs_from_server(socket):
    while True:
        try:
            new_msg = socket.recv(BUFFER_SIZE)
        except error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                continue
            else:
                print("socket error in receiving server input: " + str(e))
                break
        if not new_msg:
            break
        print(new_msg.decode())



""" The function for the third state - game mode in which two threads work in same time - one for keyboard input and the second for receiving server's messages
    Args: tcp_socket - the TCP socket used to connect the server
    Return: void
                """
def game_mode(tcp_socket):
    is_received = False
    try:
        tcp_socket.sendall(CLIENT_NAME.encode())

    except error as err_msg:
        tcp_socket.close()
        print("socket error: " + err_msg)
        return None
        
    while not is_received:
        try:
            start_game_msg = tcp_socket.recv(BUFFER_SIZE)
            print(start_game_msg.decode())
            is_received = True
            
        except error as err_msg:
            err = err_msg.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                continue
            else:
                tcp_socket.close()
                print("socket error: " + err_msg)
                return None

    fd = sys.stdin.fileno()
    get_msgs_from_server_thread = threading.Thread(target=get_msgs_from_server, args=(tcp_socket,))
    get_from_keyboard_thread = Process(target = get_from_keyboard, args=(tcp_socket,fd))
    get_from_keyboard_thread.start()
    get_msgs_from_server_thread.start()

    get_msgs_from_server_thread.join()
    get_from_keyboard_thread.terminate()
    get_from_keyboard_thread.join()
    tcp_socket.close()

    print("\nServer disconnected, listening for offer requests...")



if __name__ == "__main__":
    client_states()
