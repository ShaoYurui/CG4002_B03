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

class relay_server(threading.Thread):

    def __init__(self, ip_addr, port_num, accelerometer_data, accelerometer_queue):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip_addr, port_num))
        self.connection = None
        self.address = ""
        self.data = accelerometer_data
        self.accelerometer_queue = accelerometer_queue

        threading.Thread.__init__(self)

    def send_data(self):
        success = True
        msg = "Data successfully received at {}".format(time.ctime(time.time()))
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
            msg = data.decode("utf8")  # Decode raw bytes to UTF-8

            self.data = msg
            print(self.accelerometer_queue)

            print("Message received from relay_server: ")
            print(msg)

        except ConnectionResetError:
            print('Connection Reset')
            self.stop()

        return

    def run(self):

        self.socket.listen(1)
        self.connection, self.address = self.socket.accept()
        print("relay_server is now connected to relay_client!")
        while True:
            self.send_data()
            self.receive_data()
            self.accelerometer_queue.put(self.data)
            time.sleep(5)

""""
def main():
    ip_addr = '192.168.95.226'
    port_num = 8079
    sample_accelerometer_data = {
        "x": 1.0000,
        "y": 1.0000,
        "z": 1.0000
    }

    sample_accelerometer_data_string = json.dumps(sample_accelerometer_data)

    current_relayserver = relay_server(ip_addr, port_num, sample_accelerometer_data)

    current_relayserver.start()

    current_relayserver.join()


if __name__ == '__main__':
    main()
"""
