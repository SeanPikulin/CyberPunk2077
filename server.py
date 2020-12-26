from scapy.all import *
from socket import *
import threading
from struct import pack
from random import random
from time import sleep
import errno

group1_names = []
group2_names = []
group1_scores = []
group2_scores = []
game_connection_sockets = []
group1 = []
group2 = []
MAGIC_COOKIE = 0xfeedbeef
OFFER_MSG_TYPE = 0x02
CLIENT_OFFER_PORT = 13117
BUFFER_SIZE = 2048
FORMAT = 'IBH'
stop = threading.Event()

def server_states():
    server_welcome_socket = socket(AF_INET, SOCK_STREAM)
    server_welcome_socket.setblocking(0)
    server_welcome_socket.listen()
    while True:
        creating_a_game(server_welcome_socket)
        game_mode()

def send_offer(udp_socket, offer_msg):
    try:
        udp_socket.sendto(offer_msg, ('localhost', CLIENT_OFFER_PORT))
        sleep(1)
    except error as err_msg:
        print("socket error: " + err_msg)

def send_offers(server_port):
    offer_msg = pack(FORMAT, MAGIC_COOKIE, OFFER_MSG_TYPE, server_port)
    with socket(AF_INET, SOCK_DGRAM) as server_udp_socket:
        for _ in range(9):
            send_offers_thread = threading.Thread(target=send_offer, args=(server_udp_socket,offer_msg))
            send_offers_thread.start()
            send_offers_thread.join()

def client_in_game(conn, index, group_num):
    msg = "Welcome to Keyboard Spamming Battle Royale.\nGroup 1:\n==\n" + "".join(group1_names) + "\nGroup2:\n==\n" + "".join(group2_names) + "Start pressing keys on your keyboard as fast as you can!!"
    try:
        conn.sendall(msg.encode())
    except error as err_msg:
        conn.close()
        print("error in sending welcome message: " + err_msg)
        return

    conn.setblocking(0)
    while not is_timeout:
        try:
            conn.recv(BUFFER_SIZE)
            if group_num == 1:
                group1_scores[index] += 1
            else:
                group2_scores[index] += 1
        except error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                continue
            else:
                print("error in receiving character: " + e)
                break
    print("close client")
    conn.shutdown(SHUT_RDWR)
    conn.close()

def init_client(conn, lock1, lock2):
    try:
        client_name = conn.recv(BUFFER_SIZE)
        game_connection_sockets.append(conn)
        if random() < 0.5:
            lock1.acquire()
            print("acquired")
            client_game_thread = threading.Thread(target=client_in_game, args=(conn,len(group1), 1))
            group1_names.append(client_name.decode())
            group1_scores.append(0)
            group1.append(client_game_thread)
            lock1.release()
            print("released")
        else:
            lock2.acquire()
            print("acquired")
            client_game_thread = threading.Thread(target=client_in_game, args=(conn,len(group2), 2))
            group2_names.append(client_name.decode())
            group2_scores.append(0)
            group2.append(client_game_thread)
            lock2.release()
            print("released")
    except error as err_msg:
        conn.shutdown(SHUT_RDWR)
        conn.close()
        print("socket error: " + err_msg)

def accept_clients(welcome_socket):
    lock1 = threading.Lock()
    lock2 = threading.Lock()
    while not stop.is_set():
        try:
            conn, _ = welcome_socket.accept()
        except error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                continue
        init_client_thread = threading.Thread(target=init_client, args=(conn, lock1, lock2))
        init_client_thread.start()
    stop.clear()

def creating_a_game(welcome_socket):
    print("Server started, listening on IP address " + "localhost")
    send_offers_thread = threading.Thread(target=send_offers, args=(welcome_socket.getsockname()[1],))
    accept_clients_thread = threading.Thread(target=accept_clients, args=(welcome_socket,))
    send_offers_thread.start()
    accept_clients_thread.start()
    accept_clients_thread.join(10)
    stop.set()
    accept_clients_thread.join()
    print("game created")

def calculate_and_print_winner():
    group1_result = sum(group1_scores)
    group2_result = sum(group2_scores)
    
    result_msg = "Game over!\nGroup 1 typed in " + str(group1_result) + " characters. Group 2 typed in " + str(group2_result) + " characters.\n"
    if group1_result > group2_result:
        winner_msg = "Group 1 wins!\n\nCongratulations to the winners:\n==\n" + "".join(group1_names)
    elif group2_result > group1_result:
        winner_msg = "Group 2 wins!\n\nCongratulations to the winners:\n==\n" + "".join(group2_names)
    else:
        winner_msg = "It's a tie!\n\nCongratulations to both teams!"

    print(result_msg + winner_msg)

def game_mode():
    for thread in group1:
        thread.start()
    for thread in group2:
        thread.start()

    for thread in group1:
        thread.join(10)
    for thread in group2:
        thread.join(10)
    
    for thread in group1:
        thread.join()
    for thread in group2:
        thread.join()

    calculate_and_print_winner()

    group1.clear()
    group2.clear()
    group1_names.clear()
    group2_names.clear()
    group1_scores.clear()
    group2_scores.clear()
    game_connection_sockets.clear()

if __name__ == "__main__":
    server_states()