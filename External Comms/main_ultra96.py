import json
import pandas as pd
import os
import sys
import random as random
import time
from _socket import SHUT_RDWR
import socket
import threading
import base64
import traceback
from multiprocessing import Queue
from multiprocessing import Pipe

import concurrent.futures
#import ultra96_cnn as u96

from  relay_server import relay_server
from HardwareAI import HardwareAI
from eval_client import eval_client
from player_new import player_new

p1_accelerometer_queue = Queue()
p2_acceleromter_queue = Queue()
eval_gamestate_queue = Queue()
prediction_queue = Queue()


# eval_client Parameters
EVAL_IP                         = '127.0.0.1'
EVAL_PORT                       = 8080
GROUP_ID                        = 'B03'
SECRET_KEY                      = 1212121212121212

# relay_server_1 Parameters
RELAY_IP_1                        = '127.0.0.1'
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

class main_ultra96():
    def __init__(self, game_mode):
        self.game_mode = game_mode
        #self.cnn = u96.set_up_fpga()
        self.cnn = "cnn"

        return

    def run(self):

        my_eval_client = eval_client(EVAL_IP
                                    , EVAL_PORT
                                    , GROUP_ID
                                    , SECRET_KEY
                                    , game_mode
                                    , DEFAULT_GAME_STATE
                                    , eval_gamestate_queue
                                    , prediction_queue)

        my_relay_server = relay_server(RELAY_IP_1
                                    , RELAY_PORT_1
                                    , DEFAULT_GAME_STATE
                                    , p1_accelerometer_queue
                                    , p2_acceleromter_queue
                                    , eval_gamestate_queue)
        
        
        p1_HardwareAI = HardwareAI(p1_accelerometer_queue
                                    , prediction_queue
                                    , self.cnn
                                    , 1
                                    , 2)
        
        p2_HardwareAI = HardwareAI(p2_acceleromter_queue
                                   , prediction_queue
                                   , self.cnn
                                   , 2
                                   , 1)
        
        thread = threading.Thread(target=my_eval_client.run, daemon=True)
        thread.start()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.submit(my_relay_server.run)
            executor.submit(p1_HardwareAI.run)
            executor.submit(p2_HardwareAI.run)

        #my_eval_client.start()
        #my_relay_server.start()
        #p1_HardwareAI.start()
        #p2_HardwareAI.start()

        #my_eval_client.join()
        #my_relay_server.join()
        #p1_HardwareAI.join()
        #p2_HardwareAI.join()
        


if __name__ == '__main__':

    game_mode = int(sys.argv[1])

    my_ultra96 = main_ultra96(game_mode)
    my_ultra96.run()

