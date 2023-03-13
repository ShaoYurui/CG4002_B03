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


class relay_server(threading.Thread):

    def __init__(self, ip_addr, port_num, default_gamestate, accelerometer_queue, gamestate_queue):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip_addr, port_num))
        self.connection_list = list()
        self.connection = None
        self.address = ""
        self.debug_relay = 0
        self.dataframe = pd.DataFrame(columns=["player_id", "message_id", "x_data", "y_data", "z_data"])
        self.gamestate_data = default_gamestate
        self.accelerometer_queue = accelerometer_queue
        self.gamestate_queue = gamestate_queue

        threading.Thread.__init__(self)        


    def send_data(self):
        success = True
        self.socket.setblocking(0)
        try:
            self.gamestate_data = self.gamestate_queue.get_nowait()
            msg = json.dumps(self.gamestate_data)
            msg_length = str(len(msg))+'_'
            if self.gamestate_data == "logout":
                sys.exit()
        except Empty:
            self.socket.setblocking(0)
            return
        try:
            for conn in self.connection_list:
                self.connection = conn
                print(msg)
                print("Finished calculation at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
                self.connection.sendall(msg_length.encode("utf-8"))
                self.connection.sendall(msg.encode("utf-8"))
        except OSError:
            print("connection between relay_server and relay_client lost")
            success = False
        self.socket.setblocking(0)

        return success

    def receive_data(self):
        #self.socket.setblocking(0)
        for conn in self.connection_list:
            self.connection = conn
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
                    continue

                data = data.decode("utf-8")
                length = int(data[:-1])
                #self.socket.setblocking(1)
                self.connection.setblocking(1)
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
            except BlockingIOError:
                return
            
            msg = json.loads(data.decode("utf8"))
            #self.socket.setblocking(0)
            self.connection.setblocking(1)

            if (msg["message_type"] == 4):
                print("Right before putting into queue at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
                self.accelerometer_queue.put(msg)
                print("Put into accelerometer queue at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
            
            elif msg["message_type"] == 6:
                if ((msg["acc_x"] == 0) and (msg["acc_y"] == 0) and (msg["acc_z"] == 0)
                    and (msg["gyro_x"] == 0) and (msg["gyro_y"] == 0) and (msg["gyro_z"] == 0)):
                    continue
                else:
                    self.accelerometer_queue.put(msg)

        return

    def run(self):

        for i in range(2):
            self.socket.listen(1)
            connection, address = self.socket.accept()
            self.connection_list.append(connection)
            print("relay_server is now connected to " + str(address))

        while True:
            # Receives Accelerometer Data From relay_client for 1s
            
            self.receive_data()
            
            # Sends GameState Data To relay_client
            self.send_data()


"""
class relay_server(threading.Thread):

    def __init__(self, ip_addr, port_num, default_gamestate, accelerometer_queue, gamestate_queue):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip_addr, port_num))
        self.connection_list = list()
        self.connection = None
        self.internal_queue = Queue()
        self.address = ""
        self.debug_relay = 0
        self.dataframe = pd.DataFrame(columns=["player_id", "message_id", "x_data", "y_data", "z_data"])
        self.gamestate_data = default_gamestate
        self.accelerometer_queue = accelerometer_queue
        self.gamestate_queue = gamestate_queue

        threading.Thread.__init__(self) 

    def send_data(self, conn, gamestate_data):
        success = True
        self.socket.setblocking(0)
        try:
            msg = json.dumps(gamestate_data)
            msg_length = str(len(msg))+'_'
            if gamestate_data == "logout":
                sys.exit()
        except Empty:
            self.socket.setblocking(0)
            return
        try:
            print(msg)
            print("Finished calculation at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
            conn.sendall(msg_length.encode("utf-8"))
            conn.sendall(msg.encode("utf-8"))
        except OSError:
            print("connection between relay_server and relay_client lost")
            success = False
        self.socket.setblocking(0)

        return success

    def receive_data(self, conn):
        self.socket.setblocking(0)
        try: 
            data = b''
            while not data.endswith(b'_'):
                _d = conn.recv(1)
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from relay_server')
                return

            data = data.decode("utf-8")
            length = int(data[:-1])
            self.socket.setblocking(1)
            data = b''
            while len(data) < length:
                _d = conn.recv(length - len(data))
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from relay_server')
                self.stop()
            
            msg = json.loads(data.decode("utf8"))
            self.socket.setblocking(0)

            if (msg["message_type"] == 4):
                print("Right before putting into queue at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
                self.accelerometer_queue.put(msg)
                print("Put into accelerometer queue at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
            
            elif msg["message_type"] == 6:
                if ((msg["acc_x"] == 0) and (msg["acc_y"] == 0) and (msg["acc_z"] == 0)
                    and (msg["gyro_x"] == 0) and (msg["gyro_y"] == 0) and (msg["gyro_z"] == 0)):
                    return
                else:
                    self.accelerometer_queue.put(msg)
            
            return

        except ConnectionResetError:
            print('Connection Reset')
            self.stop()
        except BlockingIOError:
            return
    
    def client1(self, parent_conn):
        while True:
            try: 
                self.receive_data(self.connection_list[0])
                gamestate_data = self.gamestate_queue.get_nowait()
                self.internal_queue.put_nowait(gamestate_data)
                self.send_data(self.connection_list[0], gamestate_data)
            except Empty:
                self.internal_queue.put_nowait(gamestate_data)
                self.send_data(self.connection_list[0], gamestate_data)
                continue
            except BlockingIOError:
                continue
        
    def client2(self, child_conn):
        while True:
            try:
                self.receive_data(self.connection_list[1])
                gamestate_data = self.internal_queue.get_nowait()
                self.send_data(self.connection_list[1], gamestate_data)
            except BlockingIOError:
                continue
            except Full:
                continue
            except Empty:
                continue


    def run(self):

        for i in range(2):
            self.socket.listen(1)
            connection, address = self.socket.accept()
            self.connection_list.append(connection)
            print("relay_server is now connected to " + str(address))

        parent_conn, child_conn = Pipe()
        # Receives Accelerometer Data From relay_client for 1s
        c1 = Process(target=self.client1, args=(parent_conn,))
        c2 = Process(target=self.client2, args=(child_conn,))

        c1.start()
        c2.start()

        c1.join()
        c2.join()
"""



