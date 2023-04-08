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
import datetime
from multiprocessing import Process, Pipe, Queue

import time
from datetime import datetime
from queue import Empty
from queue import Full

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


#class relay_server(threading.Thread):
class relay_server():


    def __init__(self, ip_addr, port_num, default_gamestate, p1_accelerometer_queue, p2_accelerometer_queue, eval_gamestate_queue):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip_addr, port_num))
        self.connection = None
        self.address = ""
        self.gamestate_data = default_gamestate
        self.p1_accelerometer_queue = p1_accelerometer_queue
        self.p2_accelerometer_queue = p2_accelerometer_queue
        self.eval_gamestate_queue = eval_gamestate_queue

        #threading.Thread.__init__(self)        


    def send_data(self):
        success = True
        try:
            self.gamestate_data = self.eval_gamestate_queue.get_nowait()
            #print("Eval gamestate data obtained")
            msg = json.dumps(self.gamestate_data)
            msg_length = str(len(msg))+'_'
            if self.gamestate_data == "logout":
                sys.exit()
        except Empty:
            return
        try:
            # Print GameState Data for debugging
            print(msg)
            self.connection.sendall(msg_length.encode("utf-8"))
            self.connection.sendall(msg.encode("utf-8"))
            #print("Sent to relay_client at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
        except OSError:
            #print("connection between relay_server and relay_client lost")
            success = False

        return success

    def receive_data(self):
        data = b''
        self.connection.setblocking(0)
        try:
            while not data.endswith(b'_'):

                _d = self.connection.recv(1)
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from relay_server')
                return

            data = data.decode("utf-8")
            length = int(data[:-1])
            self.connection.setblocking(1)
            data = b''
            while len(data) < length:
                _d = self.connection.recv(length - len(data))
                if not _d:
                    data = b''
                    break
                data += _d
        except BlockingIOError:
            return

        msg = json.loads(data.decode("utf8"))
        self.connection.setblocking(1)

        if (msg["message_type"] == 4):
            #print("MSG 4: Right before putting into queue at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
            if msg["player_id"] == 1:
                self.p1_accelerometer_queue.put(msg)

            elif msg["player_id"] == 2:
                self.p2_accelerometer_queue.put(msg)
            #print("MSG 4: Put into accelerometer queue at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))

        elif (msg["message_type"] == 5):
            #print("MSG 5: Right before putting into queue at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
            if msg["player_id"] == 1:
                self.p2_accelerometer_queue.put(msg)

            elif msg["player_id"] == 2:
                self.p1_accelerometer_queue.put(msg)
            #print("MSG 5: Put into accelerometer queue at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
        
        elif msg["message_type"] == 6:
            #print("IMU DATA at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
            if msg["player_id"] == 1:
                self.p1_accelerometer_queue.put(msg)
            elif msg["player_id"] == 2:
                self.p2_accelerometer_queue.put(msg)

        return

    def run(self):

        self.socket.listen(1)
        connection, address = self.socket.accept()
        self.connection = connection
        print("relay_server is now connected to " + str(address))

        while True:
            #print("RELAY SERVER {conn}!!".format(conn = self.connection))
            time.sleep(0.001)
            self.send_data()
            self.receive_data()
            #time.sleep(0)


