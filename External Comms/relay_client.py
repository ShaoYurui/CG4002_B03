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
from queue import Queue

class relay_client(threading.Thread):

    def __init__(self, ip_addr, port_num, accelerometer_data):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (ip_addr, port_num)
        self.data = accelerometer_data
        self.relay_flag = 0


        threading.Thread.__init__(self)

    def send_data(self):
        success = True
        msg = json.dumps(self.data)
        msg_length = str(len(msg))+'_'

        try:
            self.socket.sendall(msg_length.encode("utf-8"))
            self.socket.sendall(msg.encode("utf-8"))
            print("Message sent to relay_server!")
        except OSError:
            print("connection between relay_client and relay_server lost")
            success = False
        return success

    def receive_data(self):
        try: 
            data = b''
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
            msg = data.decode("utf8")  # Decode raw bytes to UTF-8

            print("Message received from relay_server: ")
            print(msg)

        except ConnectionResetError:
            print('Connection Reset')
            self.stop()

        return

    def run(self):

        self.socket.connect(self.server_address)
        print("relay_client is now connected to relay_server!")
        while True:
            self.send_data()
            self.receive_data()
            self.relay_flag = 0
            time.sleep(5)

def main():
    ip_addr = '127.0.0.1'
    port_num = 8079
    sample_accelerometer_data = {
        "x": 0.0000,
        "y": 0.0000,
        "z": 0.0000
    }

    sample_accelerometer_data_string = json.dumps(sample_accelerometer_data)

    current_relay = relay_client(ip_addr, port_num, sample_accelerometer_data)

    current_relay.start()

    current_relay.join()


if __name__ == '__main__':
    main()

