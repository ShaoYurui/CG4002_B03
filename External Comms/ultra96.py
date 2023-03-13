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
from player import player

accelerometer_queue = Queue()
gamestate_queue = Queue()
prediction_queue = Queue()
eval_to_p1_queue = Queue()
p1_to_eval_queue = Queue()
eval_to_p2_queue = Queue()
p2_to_eval_queue = Queue()

relay_to_AI_conn, AI_to_relay_conn = Pipe()
relay_to_eval_conn, eval_to_relay_conn = Pipe()
AI_to_eval_conn, eval_to_AI_conn = Pipe()
eval_to_p1_conn, p1_to_eval_conn = Pipe()
eval_to_p2_conn, p2_to_eval_conn = Pipe()


# eval_client Parameters
EVAL_IP                         = '192.168.95.249'
EVAL_PORT                       = 8080
GROUP_ID                        = 'B03'
SECRET_KEY                      = 1212121212121212

# relay_server_1 Parameters
RELAY_IP_1                        = '192.168.95.249'
RELAY_PORT_1                      = 8049

"""
# relay_server_2 Parameters
RELAY_IP_2                        = '192.168.95.249'
RELAY_PORT_2                      = 8050
"""

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


class Ultra96():
    def __init__(self, game_mode):
        self.game_mode = game_mode
        threading.Thread.__init__(self)

        return

    def run(self):

        """
        my_eval_client = eval_client(EVAL_IP
                                    , EVAL_PORT
                                    , GROUP_ID
                                    , SECRET_KEY
                                    , game_mode
                                    , eval_to_relay_conn
                                    , eval_to_AI_conn
                                    , eval_to_p1_conn
                                    , eval_to_p2_conn)

        my_relay_server = relay_server(RELAY_IP
                                    , RELAY_PORT
                                    , DEFAULT_GAME_STATE
                                    , relay_to_AI_conn
                                    , relay_to_eval_conn)
        
        my_HardwareAI = HardwareAI(AI_to_relay_conn
                                    , AI_to_eval_conn)
        
        my_player1 = player(p1_to_eval_conn)
        my_player2 = player(p2_to_eval_conn)
        """
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
                                    , p2_to_eval_queue)

        my_relay_server = relay_server(RELAY_IP_1
                                    , RELAY_PORT_1
                                    , DEFAULT_GAME_STATE
                                    , accelerometer_queue
                                    , gamestate_queue)
        
        my_HardwareAI = HardwareAI(accelerometer_queue
                                    , prediction_queue)
        
        my_player1 = player(eval_to_p1_queue, p1_to_eval_queue)
        my_player2 = player(eval_to_p2_queue, p2_to_eval_queue)
        

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



if __name__ == '__main__':

    game_mode = int(sys.argv[1])

    my_ultra96 = Ultra96(game_mode)
    my_ultra96.run()

