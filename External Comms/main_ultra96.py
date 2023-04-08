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
from multiprocessing import Process

import concurrent.futures
import ultra96_cnn as u96

from  relay_server import relay_server
from HardwareAI import HardwareAI
from eval_client import eval_client
from player_new import player_new

p1_accelerometer_queue = Queue()
p2_acceleromter_queue = Queue()
p1_gamestate_queue = Queue()
p2_gamestate_queue = Queue()
p1_prediction_queue = Queue()
p2_prediction_queue = Queue()


# eval_client Parameters
EVAL_IP                         = '192.168.95.224'
EVAL_PORT                       = 8080
GROUP_ID                        = 'B03'
SECRET_KEY                      = 1212121212121212

# relay_server_1 Parameters
RELAY_IP_1                        = '192.168.95.249'
RELAY_PORT_1                      = 8049

# relay_server_2 Parameters
RELAY_IP_2                        = '192.168.95.249'
RELAY_PORT_2                      = 8050

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



if __name__ == '__main__':

    game_mode = int(sys.argv[1])
    cnn = u96.set_up_fpga()

    my_eval_client = eval_client(EVAL_IP
                                , EVAL_PORT
                                , GROUP_ID
                                , SECRET_KEY
                                , game_mode
                                , DEFAULT_GAME_STATE
                                , p1_gamestate_queue
                                , p2_gamestate_queue
                                , p1_prediction_queue
                                , p2_prediction_queue)
    
    p1_relay_server = relay_server(RELAY_IP_1
                                , RELAY_PORT_1
                                , DEFAULT_GAME_STATE
                                , p1_accelerometer_queue
                                , p2_acceleromter_queue
                                , p1_gamestate_queue)

    p2_relay_server = relay_server(RELAY_IP_2
                                , RELAY_PORT_2
                                , DEFAULT_GAME_STATE
                                , p1_accelerometer_queue
                                , p2_acceleromter_queue
                                , p2_gamestate_queue)

    p1_HardwareAI = HardwareAI(p1_accelerometer_queue
                                , p1_prediction_queue
                                , cnn
                                , 1
                                , 2)

    p2_HardwareAI = HardwareAI(p2_acceleromter_queue
                                , p2_prediction_queue
                                , cnn
                                , 2
                                , 1)

    p5 = threading.Thread(target=my_eval_client.run)
    p1 = threading.Thread(target=p1_relay_server.run)
    p3 = threading.Thread(target=p2_relay_server.run)
    p2 = threading.Thread(target=p1_HardwareAI.run)
    p4 = threading.Thread(target=p2_HardwareAI.run)

    p1.start()
    p2.start()
    p3.start()
    p4.start()
    p5.start()

    p1.join()
    p2.join()
    p3.join()
    p4.join()
    p5.join()

    print("hoho")

