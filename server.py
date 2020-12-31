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
OFFER_MSG_TYPE = b'\x02'
CLIENT_OFFER_PORT = 13117
BUFFER_SIZE = 2048
FORMAT = '!IcH'
stop = threading.Event()
group_1_str = colored("Group 1",'red')
group_2_str = colored("Group 2", 'blue')
server_ip = get_if_addr('eth1') # replace with 'eth1' / 'eth2'
time_to_wait = 10
best_players = []
best_score = 0

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
        subnet_arr = server_ip.split('.')[:-2]
        subnet_arr.append('255')
        subnet_arr.append('255')
        broadcast_ip = '.'.join(subnet_arr)
        udp_socket.sendto(offer_msg, (broadcast_ip, CLIENT_OFFER_PORT))
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
        server_udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
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
        conn_index = game_connection_sockets.index([conn, True])
        game_connection_sockets[conn_index] = [conn, False]
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
            # using sleep to avoid terminate beacuse of while loop
            sleep(0.1) 
            x = conn.recv(BUFFER_SIZE)
            if not x:
                conn.close()
                conn_index = game_connection_sockets.index([conn, True])
                game_connection_sockets[conn_index] = [conn, False]
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
                conn.close()
                conn_index = game_connection_sockets.index([conn, True])
                game_connection_sockets[conn_index] = [conn, False]
                break



""" A thread function to handle a new client
    Args: conn - the TCP socket which the client is connected to
          lock1 - a lock to synchronize the access to group 1 data
          lock2 - a lock to synchronize the access to group 2 data
    Return: void
                """
def init_client(conn, lock1, lock2):
    try:
        client_name = conn.recv(BUFFER_SIZE).decode()
        game_connection_sockets.append([conn, True])
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
        conn_index = game_connection_sockets.index([conn, True])
        game_connection_sockets[conn_index] = [conn, False]
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
            # using sleep to avoid terminate beacuse of while loop
            sleep(0.1)
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
    accept_clients_thread.join(time_to_wait)
    stop.set()
    accept_clients_thread.join()



""" A function for bonus statistic - printing the best score and the best players from each group and
    Args: no args
    Return: array of players with max score 
                """
def get_most_points_players():
    players_with_max_group1 = []
    if len(group1) != 0:
        max_score_1 = max(group1_scores)
        for i in range(len(group1_scores)):
            if group1_scores[i] == max_score_1:
                players_with_max_group1.append(group1_names[i])

        get_most_points_msg = "The best score for single competitor in " + group_1_str + colored(': ', 'red') + colored(str(max_score_1), 'red') + "\nThese are the champs who got the score: " + "".join(players_with_max_group1)
        send_to_all(get_most_points_msg)
        print(get_most_points_msg)
    else:
        max_score_1 = 0

    players_with_max_group2 = []
    if len(group2) != 0:
        max_score_2 = max(group2_scores)
        for i in range(len(group2_scores)):
            if group2_scores[i] == max_score_2:
                players_with_max_group2.append(group2_names[i])

        get_most_points_msg = "The best score for single competitor in " + group_2_str + colored(': ', 'blue') + colored(str(max_score_2), 'blue') + "\nThese are the champs who got the score: " + "".join(players_with_max_group2)
        send_to_all(get_most_points_msg)
        print(get_most_points_msg)
    else:
        max_score_2 = 0
    
    if max_score_1 > max_score_2:
        return players_with_max_group1, max_score_1
    
    elif max_score_2 > max_score_1:
        return players_with_max_group2, max_score_2
    
    else:
        return players_with_max_group1 + players_with_max_group2, max_score_1


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
        winner_msg = "It's a tie!\n\nCongratulations to both teams!\n"
    msg = result_msg + winner_msg
    send_to_all(msg)
    print(msg)



""" The function for updating the best players ever statistics
    Args: curr_max_arr: last game's best players
          curr_max_score: last game's best score 
    Return: void
                """
def update_best_players(curr_max_arr, curr_max_score):
    global best_score
    global best_players
    if curr_max_score > best_score:
        best_score = curr_max_score
        best_players = curr_max_arr

    elif curr_max_score == best_score:
        best_players = list(set(best_players + curr_max_arr))



""" A function for sending data to all of the connected clients
    Args: msg - the message to send
    Return: void
                """
def send_to_all(msg):
    try:
        for socket_two_list in game_connection_sockets:
            if socket_two_list[1]:
                socket_two_list[0].sendall(msg.encode())
    except error as err:
        print("error sending message: " + err)



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
        thread.join(time_to_wait)
    for thread in group2:
        thread.join(time_to_wait)
    
    stop.set()

    for thread in group1:
        thread.join()
    for thread in group2:
        thread.join()

    stop.clear()
    calculate_and_print_winner()
    statistics = colored("\nStatisics from the game\n\n", 'yellow', attrs=['underline'])
    send_to_all(statistics)
    print(statistics)
    curr_max_arr, curr_max_score = get_most_points_players()
    update_best_players(curr_max_arr, curr_max_score)
    best_players_msg = "\nCurrent best players ever (with score " + colored(str(best_score), attrs=['bold']) + "):\n" + "".join(best_players)
    send_to_all(best_players_msg)
    print(best_players_msg)

    seperator = colored("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n", 'magenta')
    send_to_all(seperator)
    print(seperator)
    for socket, isOpen in game_connection_sockets:
        if isOpen:
            socket.close()

    group1.clear()
    group2.clear()
    group1_names.clear()
    group2_names.clear()
    group1_scores.clear()
    group2_scores.clear()
    game_connection_sockets.clear()



if __name__ == "__main__":
    server_states()
