from scapy.all import *
from socket import *
import threading
from struct import pack
from random import random
from time import sleep
import errno
import sys 
from termcolor import colored, cprint

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
group_1_str = colored("Group 1",'red')
group_2_str = colored("Group 2", 'blue')
server_ip = 'localhost'

""" The main function for transition between the server's states - first creating a game, then enter game mode
    Args: no args
    Return: void
                """
def server_states():
    server_welcome_socket = socket(AF_INET, SOCK_STREAM)
    server_welcome_socket.setblocking(0)
    server_welcome_socket.listen()
    while True:
        creating_a_game(server_welcome_socket)
        game_mode()
    server_welcome_socket.close()



""" A thread function for sending a single offer 
    Args: udp_socket - the socket for broadcasting
          offer_msg - the message (the format detailed in the assignment)
    Return: void
                """
def send_offer(udp_socket, offer_msg):
    try:
        udp_socket.sendto(offer_msg, (server_ip, CLIENT_OFFER_PORT))
        sleep(1)
    except error as err_msg:
        print("socket error: " + err_msg)



""" The thread function where the server sends offers through UDP 
    Args: server_port - the TCP port to which the client needs to connect
    Return: void
                """
def send_offers(server_port):
    offer_msg = pack(FORMAT, MAGIC_COOKIE, OFFER_MSG_TYPE, server_port)
    with socket(AF_INET, SOCK_DGRAM) as server_udp_socket:
        for _ in range(9):
            send_offers_thread = threading.Thread(target=send_offer, args=(server_udp_socket,offer_msg))
            send_offers_thread.start()
            send_offers_thread.join()



""" A thread function that will be activated per client in the client's game mode
    Args: conn - the TCP socket which the client is connected to
          index - the pre-defined index of the client in the game data lists
          group_num - the group that the client was allocated by the server
    Return: void
                """
def client_in_game(conn, index, group_num):
    msg = "Welcome to Keyboard Spamming Battle Royale.\n" + group_1_str + colored(":", "red") +"\n==\n" + "".join(group1_names) + "\n" + group_2_str + colored(":", "blue") +"\n==\n" + "".join(group2_names) + "\nStart pressing keys on your keyboard as fast as you can!!"
    try:
        conn.sendall(msg.encode())
    except error as err_msg:
        conn.close()
        print("error in sending welcome message: " + err_msg)
        if group_num == 1:
            name = group1_names[index]
        else:
            name = group2_names[index]
        print("The client " + name + " disconnected from the server..." )
        return

    conn.setblocking(0)
    while not stop.is_set():
        try:
            x = conn.recv(BUFFER_SIZE)
            if not x:
                break
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

                if group_num == 1:
                    name = group1_names[index]
                else:
                    name = group2_names[index]
                print("The client " + name + " disconnected from the server..." )
                break
    conn.close()



""" A thread function to handle a new client
    Args: conn - the TCP socket which the client is connected to
          lock1 - a lock to synchronize the access to group 1 data
          lock2 - a lock to synchronize the access to group 2 data
    Return: void
                """
def init_client(conn, lock1, lock2):
    try:
        client_name = conn.recv(BUFFER_SIZE).decode()
        game_connection_sockets.append(conn)
        if random() < 0.5:
            lock1.acquire()
            client_game_thread = threading.Thread(target=client_in_game, args=(conn,len(group1), 1))
            group1_names.append(colored(client_name, 'cyan'))
            group1_scores.append(0)
            group1.append(client_game_thread)
            lock1.release()
        else:
            lock2.acquire()
            client_game_thread = threading.Thread(target=client_in_game, args=(conn,len(group2), 2))
            group2_names.append(colored(client_name, 'cyan'))
            group2_scores.append(0)
            group2.append(client_game_thread)
            lock2.release()
    except error as err_msg:
        conn.close()
        print("socket error: " + err_msg)
        print("The client " + client_name + " disconnected from the server..." )



""" A function used when creating a game - to accept the players and call their threads 
    Args: welcome_socket - the welcome socket of the Server - to accept clients and handle their connections 
    Return: void
                """
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
            else:
                print("The error is: " + err)
                sys.exit(0)
        init_client_thread = threading.Thread(target=init_client, args=(conn, lock1, lock2))
        init_client_thread.start()
    stop.clear()



""" The function for the first state - the server is building a game by broadcasting offers through UDP
    Args: welcome_socket - the TCP master socket to accept new clients
    Return: void
                """
def creating_a_game(welcome_socket):
    print("Server started, listening on IP address: " + colored(server_ip, attrs=['bold']))
    send_offers_thread = threading.Thread(target=send_offers, args=(welcome_socket.getsockname()[1],))
    accept_clients_thread = threading.Thread(target=accept_clients, args=(welcome_socket,))
    send_offers_thread.start()
    accept_clients_thread.start()
    accept_clients_thread.join(10)
    stop.set()
    accept_clients_thread.join()



""" A function for bonus statistic - printing the best score and the best players from each group and
    Args: no args
    Return: void
                """
def get_most_points_players():
    if len(group1) != 0:
        max_score_1 = max(group1_scores)
        players_with_max = []
        for i in range(len(group1_scores)):
            if group1_scores[i] == max_score_1:
                players_with_max.append(group1_names[i])

        print("The best score for single competitor in " + group_1_str + colored(': ', 'red') + colored(str(max_score_1), 'red'))
        print("These are the champs who got the score: " + "".join(players_with_max))

    if len(group2) != 0:
        max_score_2 = max(group2_scores)
        players_with_max = []
        for i in range(len(group2_scores)):
            if group2_scores[i] == max_score_2:
                players_with_max.append(group2_names[i])

        print("The best score for single competitor in " + group_2_str + colored(': ', 'blue') + colored(str(max_score_2), 'blue'))
        print("These are the champs who got the score: " + "".join(players_with_max))



""" A function that is used in the end of each game - calculating the points and declaring the winner
    Args: no args
    Return: void
                """
def calculate_and_print_winner():
    group1_result = sum(group1_scores)
    group2_result = sum(group2_scores)
    
    result_msg = "\nGame over!\n" + group_1_str + " typed in " + str(group1_result) + " characters. " + group_2_str + " typed in " + str(group2_result) + " characters.\n"
    if group1_result > group2_result:
        winner_msg = group_1_str + " wins!\n\nCongratulations to the winners:\n==\n" + "".join(group1_names)
    elif group2_result > group1_result:
        winner_msg = group_2_str + " wins!\n\nCongratulations to the winners:\n==\n" + "".join(group2_names)
    else:
        winner_msg = "It's a tie!\n\nCongratulations to both teams!"

    print(result_msg + winner_msg)



""" The function for the second state - the server activates the in_game clients' threads and print statistics
    Args: no args
    Return: void
                """
def game_mode():
    print("Starting a game! Good luck to both teams!")
    for thread in group1:
        thread.start()
    for thread in group2:
        thread.start()

    for thread in group1:
        thread.join(10)
    for thread in group2:
        thread.join(10)
    
    stop.set()

    for thread in group1:
        thread.join()
    for thread in group2:
        thread.join()

    stop.clear()
    calculate_and_print_winner()
    cprint("Statisics from the game", 'yellow', attrs=['underline'])
    get_most_points_players()

    group1.clear()
    group2.clear()
    group1_names.clear()
    group2_names.clear()
    group1_scores.clear()
    group2_scores.clear()
    game_connection_sockets.clear()



if __name__ == "__main__":
    server_states()