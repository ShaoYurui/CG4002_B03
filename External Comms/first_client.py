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
from queue import Empty
from multiprocessing import Pipe


class relay_client(threading.Thread):

    def __init__(self, ip_addr, port_num):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (ip_addr, port_num)
        self.accelerometer_data = None
        self.gamestate_data = None

        threading.Thread.__init__(self)

    def send_data(self):
        success = True
        # Sends Sample Data (For Now)
        self.accelerometer_data = {"player_id": 1, "message_type": 6, "acc_x": 0.5, "acc_y": 0.5, "acc_z": 0.5, "gyro_x": 0.5, "gyro_y": 0.5, "gyro_z": 0.5}
        
        msg = json.dumps(self.accelerometer_data)
        msg_length = str(len(msg))+'_'

        try:
            self.socket.sendall(msg_length.encode("utf-8"))
            self.socket.sendall(msg.encode("utf-8"))
        except OSError:
            return
        return success

    def receive_data(self):
        try: 
            data = b''
            self.socket.setblocking(0)
            while not data.endswith(b'_'):
                _d = self.socket.recv(1)
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from relay_server')
                self.stop()

            data = data.decode("utf-8")
            length = int(data[:-1])
            self.socket.setblocking(1)

            data = b''
            while len(data) < length:
                _d = self.socket.recv(length - len(data))
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from relay_server')
                self.stop()
            msg = json.loads(data.decode("utf8"))  # Decode raw bytes to UTF-8
            self.socket.setblocking(1)

            self.gamestate_data = msg
            print(self.gamestate_data)

        except ConnectionResetError:
            print('Connection Reset')
            self.stop()
        except BlockingIOError:
            return

        return

    def run(self):

        self.socket.connect(self.server_address)
        print("relay_client is now connected to relay_server!")
        while True:
            # Send Data for 1s

            self.send_data()
            time.sleep(0.02)
            
            # Receive Data
            self.receive_data()

def main():
    ip_addr = '127.0.0.1'
    port_num = 8049

    current_relay = relay_client(ip_addr, port_num)

    current_relay.start()
    current_relay.join()


if __name__ == '__main__':
    main()

