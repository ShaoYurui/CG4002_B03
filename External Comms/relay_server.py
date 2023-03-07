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
import datetime
from multiprocessing import Queue
from multiprocessing import Pipe

from queue import Empty

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

class relay_server(threading.Thread):

    def __init__(self, ip_addr, port_num, default_gamestate, relay_to_AI_conn, relay_to_eval_conn):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip_addr, port_num))
        self.connection = None
        self.address = ""
        self.dataframe = pd.DataFrame(columns=["player_id", "message_id", "x_data", "y_data", "z_data"])
        self.gamestate_data = default_gamestate
        self.relay_to_AI_conn = relay_to_AI_conn
        self.relay_to_eval_conn = relay_to_eval_conn

        threading.Thread.__init__(self)        

    def send_data(self):
        success = True
        try:
            self.gamestate_data = self.relay_to_eval_conn.recv()
            msg = json.dumps(self.gamestate_data)
            msg_length = str(len(msg))+'_'
        except Empty:
            msg = json.dumps(self.gamestate_data)
            msg_length = str(len(msg))+'_'

        try:
            self.connection.sendall(msg_length.encode("utf-8"))
            self.connection.sendall(msg.encode("utf-8"))
        except OSError:
            print("connection between relay_server and relay_client lost")
            success = False

        return success

    def receive_data(self):
        try: 
            data = b''
            while not data.endswith(b'_'):
                _d = self.connection.recv(1)
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from relay_server')
                self.stop()

            data = data.decode("utf-8")
            length = int(data[:-1])

            data = b''
            while len(data) < length:
                _d = self.connection.recv(length - len(data))
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from relay_server')
                self.stop()
            
            msg = json.loads(data.decode("utf8"))
            msg_df = pd.DataFrame([msg])
            self.dataframe = pd.concat([self.dataframe, msg_df], ignore_index=True)

            return

        except ConnectionResetError:
            print('Connection Reset')
            self.stop()

        return None

    def send_hardware_AI(self):
        # 1 = shooting, 2 = shield, 3 = grenade, 4 = reload
        self.relay_to_AI_conn.send(self.dataframe)
        return

    def run(self):

        self.socket.listen(1)
        self.connection, self.address = self.socket.accept()
        print("relay_server is now connected to relay_client!")

        while True:
            # Receives Accelerometer Data From relay_client for 1s
            endTime = datetime.datetime.now() + datetime.timedelta(microseconds=1000)
            while datetime.datetime.now() <= endTime:
                try:
                    self.receive_data()
                except Empty:
                    continue
            
            print("From relay_server: Accelerometer Data received!")

            # Send dataframe to Hardware AI
            self.send_hardware_AI()

            print("From relay_server: Accelerometer Data sent to Hardware AI!")

            # Empty Dataframe
            self.dataframe = pd.DataFrame(columns=["player_id", "message_id", "x_data", "y_data", "z_data"])

            # Sends GameState Data To relay_client
            self.send_data()


"""
class relay_server(threading.Thread):

    def __init__(self, ip_addr, port_num, default_gamestate, accelerometer_queue, gamestate_queue):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip_addr, port_num))
        self.connection = None
        self.address = ""
        self.dataframe = pd.DataFrame(columns=["player_id", "message_id", "x_data", "y_data", "z_data"])
        self.gamestate_data = default_gamestate
        self.accelerometer_queue = accelerometer_queue
        self.gamestate_queue = gamestate_queue

        threading.Thread.__init__(self)        

    def send_data(self):
        success = True
        try:
            self.gamestate_data = self.gamestate_queue.get()
            msg = json.dumps(self.gamestate_data)
            msg_length = str(len(msg))+'_'
        except Empty:
            msg = json.dumps(self.gamestate_data)
            msg_length = str(len(msg))+'_'

        try:
            self.connection.sendall(msg_length.encode("utf-8"))
            self.connection.sendall(msg.encode("utf-8"))
        except OSError:
            print("connection between relay_server and relay_client lost")
            success = False

        return success

    def receive_data(self):
        try: 
            data = b''
            while not data.endswith(b'_'):
                _d = self.connection.recv(1)
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from relay_server')
                self.stop()

            data = data.decode("utf-8")
            length = int(data[:-1])

            data = b''
            while len(data) < length:
                _d = self.connection.recv(length - len(data))
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from relay_server')
                self.stop()
            
            msg = json.loads(data.decode("utf8"))
            msg_df = pd.DataFrame([msg])
            self.dataframe = pd.concat([self.dataframe, msg_df], ignore_index=True)

            return

        except ConnectionResetError:
            print('Connection Reset')
            self.stop()

        return None

    def send_hardware_AI(self):
        # 1 = shooting, 2 = shield, 3 = grenade, 4 = reload
        self.accelerometer_queue.put(self.dataframe)
        return

    def run(self):

        self.socket.listen(1)
        self.connection, self.address = self.socket.accept()
        print("relay_server is now connected to relay_client!")

        while True:
            # Receives Accelerometer Data From relay_client for 1s
            endTime = datetime.datetime.now() + datetime.timedelta(microseconds=1000)
            while datetime.datetime.now() <= endTime:
                try:
                    self.receive_data()
                except Empty:
                    continue
            
            print("From relay_server: Accelerometer Data received!")

            # Send dataframe to Hardware AI
            self.send_hardware_AI()

            print("From relay_server: Accelerometer Data sent to Hardware AI!")

            # Empty Dataframe
            self.dataframe = pd.DataFrame(columns=["player_id", "message_id", "x_data", "y_data", "z_data"])

            # Sends GameState Data To relay_client
            self.send_data()
"""

"""
def main():
    ip_addr = '192.168.95.249'
    port_num = 8079

    accelerometer_queue = Queue()
    gamestate_queue = Queue()

    gamestate_queue.put(DEFAULT_GAME_STATE)

    current_relayserver = relay_server(ip_addr, port_num, DEFAULT_GAME_STATE, accelerometer_queue, gamestate_queue)

    current_relayserver.start()
    current_relayserver.join()


if __name__ == '__main__':
    main()
"""

