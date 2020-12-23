from scapy.all import *
from socket import *
import threading
from struct import pack, unpack
from random import random

GROUP_1_NAMES = []
GROUP_2_NAMES = []
GROUP_1_SCORES = []
GROUP_2_SCORES = []
GAME_CONNECTION_SOCKETS = []
GROUP_1 = []
GROUP_2 = []
MAGIC_COOKIE = 0xfeedbeef
OFFER_MSG_TYPE = 0x02
client_offer_port = 13117
BUFFER_SIZE = 2048

def server_states():
    server_welcome_socket = socket(AF_INET, SOCK_STREAM)
    while True:
        creating_a_game(server_welcome_socket)
        game_mode()

def send_offer(udp_socket, offer_msg):
    try:
        udp_socket.sendto(offer_msg, ("localhost", client_offer_port))
    except error as err_msg:
        print("socket error: " + err_msg)

def send_offers(server_port):
    offer_msg = bytes(MAGIC_COOKIE) + bytes(OFFER_MSG_TYPE) + bytes(server_port)
    with socket(AF_INET, SOCK_DGRAM) as server_udp_socket:
        for _ in range(9):
            send_offers_thread = threading.Timer(interval=1.0, function=send_offer, args=(server_udp_socket,offer_msg))
            send_offers_thread.start()
            send_offers_thread.join()

def client_in_game(conn, index, group_num):
    msg = "Welcome to Keyboard Spamming Battle Royale.\nGroup 1:\n==\n" + "".join(GROUP_1_NAMES) + "\nGroup2:\n==\n" + "".join(GROUP_2_NAMES) + "Start pressing keys on your keyboard as fast as you can!!"
    try:
        conn.sendall(msg.encode())
    except error as err_msg:
        conn.close()
        print("error in sending welcome message: " + err_msg)
        return
    
    try:
        while True:
            conn.recv(BUFFER_SIZE)
            if group_num == 1:
                GROUP_1_SCORES[index] += 1
            else:
                GROUP_2_SCORES[index] += 1
    except error as err_msg:
        conn.close()
        print("error in receiving character: " + err_msg)
       

def init_client(conn, lock1, lock2):
    try:
        client_name = conn.recv(BUFFER_SIZE)
        GAME_CONNECTION_SOCKETS.append(conn)
        if random() < 0.5:
            lock1.acquire()
            client_game_thread = threading.Timer(interval=10.0, function=client_in_game, args=(conn,len(GROUP_1), 1))
            GROUP_1_NAMES.append(client_name)
            GROUP_1_SCORES.append(0)
            GROUP_1.append(client_game_thread)
            lock1.release()
        else:
            lock2.acquire()
            client_game_thread = threading.Timer(interval=10.0, function=client_in_game, args=(conn,len(GROUP_2), 2))
            GROUP_2_NAMES.append(client_name)
            GROUP_2_SCORES.append(0)
            GROUP_2.append(client_game_thread)
            lock2.release()
    except error as err_msg:
        conn.close()
        print("socket error: " + err_msg)

def accept_clients(welcome_socket):
    lock1 = threading.Lock()
    lock2 = threading.Lock()
    while True:
        welcome_socket.listen()
        conn, _ = welcome_socket.accept()
        init_client_thread = threading.Thread(target=init_client, args=(conn, lock1, lock2))
        init_client_thread.start()

def creating_a_game(welcome_socket):
        
    send_offers_thread = threading.Thread(target=send_offers, args=(welcome_socket.getsockname()[1],))
    accept_clients_thread = threading.Timer(interval=10.0, function=accept_clients, args=(welcome_socket,))
    send_offers_thread.start()
    accept_clients_thread.start()
    accept_clients_thread.join()

def calculate_and_print_winner():
    group_1_result = sum(GROUP_1_SCORES)
    group_2_result = sum(GROUP_2_SCORES)
    
    result_msg = "Game over!\nGroup 1 typed in " + str(group_1_result) + "characters. Group 2 typed in " + str(group_2_result) + " characters.\n"
    if group_1_result > group_2_result:
        winner_msg = "Group 1 wins!\n\nCongratulations to the winners:\n==\n" + "".join(GROUP_1_NAMES)
    elif group_2_result > group_1_result:
        winner_msg = "Group 2 wins!\n\nCongratulations to the winners:\n==\n" + "".join(GROUP_2_NAMES)
    else:
        winner_msg = "It's a tie!\n\nCongratulations to both teams!"

    print(result_msg + winner_msg)

def game_mode():
    for thread in GROUP_1:
        thread.start()
        
    for thread in GROUP_2:
        thread.start()

    for thread in GROUP_1:
        thread.join()
        
    for thread in GROUP_2:
        thread.join()

    calculate_and_print_winner()
    for conn in GAME_CONNECTION_SOCKETS:
        conn.close()

    GROUP_1.clear()
    GROUP_2.clear()
    GROUP_1_NAMES.clear()
    GROUP_2_NAMES.clear()
    GROUP_1_SCORES.clear()
    GROUP_2_SCORES.clear()
    GAME_CONNECTION_SOCKETS.clear()

if __name__ == "__main__":
    server_states()