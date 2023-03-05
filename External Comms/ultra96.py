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

from eval_client import eval_client
from  relay_server import relay_server
from HardwareAI import HardwareAI

# Queues

accelerometer_queue = Queue()
gamestate_queue = Queue()
prediction_queue = Queue()
p1_queue = Queue()
p2_queue = Queue()

# eval_client Parameters
EVAL_IP                         = '192.168.95.249'
EVAL_PORT                       = 8080
GROUP_ID                        = 'B03'
SECRET_KEY                      = 1212121212121212

# relay_server Parameters
RELAY_IP                        = '192.168.95.249'
RELAY_PORT                      = 8079

# Default Game State
DEFAULT_GAME_STATE              = {
                                        "p1": {
                                            "hp": 100,
                                            "action": "none",
                                            "bullets": 6,
                                            "grenades": 2,
                                            "shield_time": 10,
                                            "shield_health": 30,
                                            "num_deaths": 0,
                                            "num_shield": 3
                                        },
                                        "p2": {
                                            "hp": 100,
                                            "action": "none",
                                            "bullets": 6,
                                            "grenades": 2,
                                            "shield_time": 10,
                                            "shield_health": 30,
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
        my_eval_client = eval_client(EVAL_IP
                                    , EVAL_PORT
                                    , GROUP_ID
                                    , SECRET_KEY
                                    , game_mode
                                    , gamestate_queue
                                    , prediction_queue
                                    , p1_queue
                                    , p2_queue)

        my_relay_server = relay_server(RELAY_IP
                                    , RELAY_PORT
                                    , DEFAULT_GAME_STATE
                                    , accelerometer_queue
                                    , gamestate_queue)
        
        my_HardwareAI = HardwareAI(accelerometer_queue
                                    , prediction_queue)

        my_eval_client.start()
        my_relay_server.start()
        my_HardwareAI.start()

        my_eval_client.join()
        my_relay_server.join()
        my_HardwareAI.start()


if __name__ == '__main__':
    game_mode = sys.argv[1]

    my_ultra96 = Ultra96(game_mode)
    my_ultra96.run()

