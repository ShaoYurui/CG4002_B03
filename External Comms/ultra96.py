import json
import pandas as pd
import os
import sys
import random as random
import time
import tkinter as tk
from _socket import SHUT_RDWR
import socket
import threading
import base64
import traceback
from multiprocessing import Queue
from multiprocessing import Pipe

from eval_client import eval_client
from  relay_server import relay_server
from HardwareAI import HardwareAI
from SoftwareAI import SoftwareAI
from player import player
from eval_client2 import eval_client2
from player_new import player_new

accelerometer_queue = Queue()
eval_gamestate_queue = Queue()
calc_gamestate_queue = Queue()
prediction_queue = Queue()
eval_to_p1_queue = Queue()
p1_to_eval_queue = Queue()
eval_to_p2_queue = Queue()
p2_to_eval_queue = Queue()
fasttrack_queue = Queue()
eval_to_p1_update_queue = Queue()
eval_to_p2_update_queue = Queue()

relay_to_AI_conn, AI_to_relay_conn = Pipe()
relay_to_eval_conn, eval_to_relay_conn = Pipe()
AI_to_eval_conn, eval_to_AI_conn = Pipe()
eval_to_p1_conn, p1_to_eval_conn = Pipe()
eval_to_p2_conn, p2_to_eval_conn = Pipe()


# eval_client Parameters
EVAL_IP                         = '137.132.92.184'
EVAL_PORT                       = 9999
GROUP_ID                        = 'B03'
SECRET_KEY                      = 1212121212121212

# relay_server_1 Parameters
RELAY_IP_1                        = '192.168.95.249'
RELAY_PORT_1                      = 8049

# Default Game State
DEFAULT_GAME_STATE              = {
                                        "p1": {
                                            "hp": 100,
                                            "action": "none",
                                            "bullets": 6,
                                            "grenades": 2,
                                            "shield_time": 0,
                                            "shield_health": 0,
                                            "num_deaths": 0,
                                            "num_shield": 3
                                        },
                                        "p2": {
                                            "hp": 100,
                                            "action": "none",
                                            "bullets": 6,
                                            "grenades": 2,
                                            "shield_time": 0,
                                            "shield_health": 0,
                                            "num_deaths": 0,
                                            "num_shield": 3
                                        }
                                    }

"""
class Ultra96():
    def __init__(self, game_mode):
        self.game_mode = game_mode
        threading.Thread.__init__(self)

        return

    def run(self):

        my_eval_client = eval_client(EVAL_IP
                                    , EVAL_PORT
                                    , GROUP_ID
                                    , SECRET_KEY
                                    , game_mode
                                    , DEFAULT_GAME_STATE
                                    , gamestate_queue
                                    , prediction_queue
                                    , eval_to_p1_queue
                                    , eval_to_p2_queue
                                    , p1_to_eval_queue
                                    , p2_to_eval_queue
                                    , eval_to_p1_update_queue
                                    , eval_to_p2_update_queue)

        my_relay_server = relay_server(RELAY_IP_1
                                    , RELAY_PORT_1
                                    , DEFAULT_GAME_STATE
                                    , accelerometer_queue
                                    , gamestate_queue)
        
        my_HardwareAI = HardwareAI(accelerometer_queue
                                    , prediction_queue)
        
        my_player1 = player(eval_to_p1_queue, p1_to_eval_queue, eval_to_p1_update_queue)
        my_player2 = player(eval_to_p2_queue, p2_to_eval_queue, eval_to_p2_update_queue)
        

        my_eval_client.start()
        my_relay_server.start()
        my_HardwareAI.start()
        my_player1.start()
        my_player2.start()

        my_eval_client.join()
        my_relay_server.join()
        # my_relay_server_2.join()
        my_HardwareAI.join()
        my_player1.join()
        my_player2.join()
"""

class Ultra96():
    def __init__(self, game_mode):
        self.game_mode = game_mode
        threading.Thread.__init__(self)

        return

    def run(self):

        my_eval_client = eval_client2(EVAL_IP
                                    , EVAL_PORT
                                    , GROUP_ID
                                    , SECRET_KEY
                                    , game_mode
                                    , DEFAULT_GAME_STATE
                                    , calc_gamestate_queue
                                    , eval_gamestate_queue
                                    , prediction_queue)

        my_relay_server = relay_server(RELAY_IP_1
                                    , RELAY_PORT_1
                                    , DEFAULT_GAME_STATE
                                    , accelerometer_queue
                                    , calc_gamestate_queue
                                    , eval_gamestate_queue)
        
        
        my_HardwareAI = HardwareAI(accelerometer_queue
                                    , prediction_queue)
        
        """
        my_SoftwareAI = SoftwareAI(accelerometer_queue
                                   , prediction_queue)
        """

        my_eval_client.start()
        my_relay_server.start()
        #my_SoftwareAI.start()

        my_HardwareAI.start()

        my_eval_client.join()
        my_relay_server.join()
        #my_SoftwareAI.join()

        my_HardwareAI.join()



if __name__ == '__main__':

    game_mode = int(sys.argv[1])

    my_ultra96 = Ultra96(game_mode)
    my_ultra96.run()

