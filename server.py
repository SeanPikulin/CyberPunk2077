from socket import *
import threading
from struct import pack, unpack
from random import randint


GROUP_1 = []
GROUP_2 = []

def server_states():
    try:
        while True:
            creating_a_game()
            game_mode()


