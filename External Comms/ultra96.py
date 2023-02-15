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
from visualizer_server import visualizer_server

# Queues

accelerometer_queue = Queue()
gamestate_queue = Queue()

# eval_client Parameters
EVAL_IP                         = '192.168.95.226'
EVAL_PORT                       = 8080
GROUP_ID                        = 'B03'
SECRET_KEY                      = 1212121212121212

# relay_server Parameters
RELAY_IP                        = '192.168.95.226'
RELAY_PORT                      = 8079

# visualizer_server Parameters
VISUALIZER_BROKER               = 'broker.emqx.io'
VISUALIZER_PORT                 = 1883
VISUALIZER_TOPIC                = "ultra96"
VISUALIZER_USERNAME             = "KaiserHuang"
VISUALIZER_PASSWORD             = "public"

# sample accelerometer data
SAMPLE_ACCELEROMETER_DATA       = {
                                        "x": 1.0000,
                                        "y": 1.0000,
                                        "z": 1.0000
                                    }

# Default Game State
DEFAULT_GAME_STATE              = {
                                        "p1": {
                                            "hp": 10,
                                            "action": "grenade",
                                            "bullets": 1,
                                            "grenades": 1,
                                            "shield_time": 0,
                                            "shield_health": 3,
                                            "num_deaths": 1,
                                            "num_shield": 0
                                        },
                                        "p2": {
                                            "hp": 100,
                                            "action": "shield",
                                            "bullets": 2,
                                            "grenades": 2,
                                            "shield_time": 1,
                                            "shield_health": 0,
                                            "num_deaths": 5,
                                            "num_shield": 2
                                        }
                                    }



class Ultra96():
    def __init__(self):
        threading.Thread.__init__(self)

        return

    def run(self):

        my_eval_client = eval_client(EVAL_IP
                                    , EVAL_PORT
                                    , GROUP_ID
                                    , SECRET_KEY
                                    , DEFAULT_GAME_STATE
                                    , gamestate_queue)

        my_relay_server = relay_server(RELAY_IP
                                    , RELAY_PORT
                                    , SAMPLE_ACCELEROMETER_DATA
                                    , accelerometer_queue)

        my_visualizer_server = visualizer_server(VISUALIZER_BROKER
                                                , VISUALIZER_PORT
                                                , VISUALIZER_TOPIC
                                                , VISUALIZER_USERNAME
                                                , VISUALIZER_PASSWORD
                                                , gamestate_queue)

        my_eval_client.start()
        my_relay_server.start()
        my_visualizer_server.start()

        my_eval_client.join()
        my_relay_server.join()
        my_visualizer_server.join()





if __name__ == '__main__':
    my_ultra96 = Ultra96()
    my_ultra96.run()

