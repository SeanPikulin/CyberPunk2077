from scapy.all import *
from socket import *
import threading
from struct import pack, unpack
from random import random

GROUP_1_NAMES = []
GROUP_2_NAMES = []
GROUP_1 = []
GROUP_2 = []
MAGIC_COOKIE = 0xfeedbeef
OFFER_MSG_TYPE = 0x02
client_offer_port = 13117
BUFFER_SIZE = 2048

def server_states():
    try:
        server_welcome_socket = socket(AF_INET, SOCK_STREAM)
        while True:
            creating_a_game(server_welcome_socket)
            game_mode()
    except error as err_msg:
        pass

def send_offer(udp_socket, offer_msg):
    udp_socket.sendto(offer_msg, ("localhost", client_offer_port))

def send_offers(server_port):
    offer_msg = bytes(MAGIC_COOKIE) + bytes(OFFER_MSG_TYPE) + bytes(server_port)
    with socket(AF_INET, SOCK_DGRAM) as server_udp_socket:
        for _ in range(9):
            send_offers_thread = threading.Timer(interval=1.0, function=send_offer, args=(server_udp_socket,offer_msg))
            send_offers_thread.start()
            send_offers_thread.join()

def client_in_game():
    pass

def init_client(conn, lock1, lock2):
    try:
        client_name = conn.recv(BUFFER_SIZE)
        client_game_thread = threading.Thread(target=client_in_game)
        if random() < 0.5:
            lock1.acquire()
            GROUP_1_NAMES.append(client_name)
            GROUP_1.append((client_game_thread, conn, 0))
            lock1.release()
        else:
            lock2.acquire()
            GROUP_2_NAMES.append(client_name)
            GROUP_2.append((client_game_thread, conn, 0))
            lock2.release()
    except error:
        pass

def accept_clients(welcome_socket):
    lock1 = threading.Lock()
    lock2 = threading.Lock()
    while True:
        welcome_socket.listen()
        conn, addr = welcome_socket.accept()
        init_client_thread = threading.Thread(target=init_client, args=(conn, lock1, lock2))
        init_client_thread.start()

def creating_a_game(welcome_socket): 
    send_offers_thread = threading.Thread(target=send_offers, args=welcome_socket.getsockname()[1])
    accept_clients_thread = threading.Timer(interval=10.0, function=accept_clients, args=welcome_socket)
    send_offers_thread.start()
    accept_clients_thread.start()
    accept_clients_thread.join()

    
    

def game_mode():
    pass