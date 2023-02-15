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
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto import Random
import traceback
from multiprocessing import Queue

class eval_client(threading.Thread):

    def __init__(self, ip_addr, port_num, group_id, secret_key, default_game_state, gamestate_queue):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (ip_addr, port_num)
        self.secret_key = secret_key
        self.data = default_game_state
        self.gamestate_queue = gamestate_queue

        threading.Thread.__init__(self)
    

    def _encrypt_message(self, plaintext):
        print("Plaintext to be sent to eval_server: ", plaintext)
        iv = Random.new().read(AES.block_size)
        secret_key = bytes(str(self.secret_key), encoding="utf8")
        cipher = AES.new(secret_key, AES.MODE_CBC, iv)

        ciphertext = base64.b64encode(iv + cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size)))
        return ciphertext

    def send_data(self):
        success = True
        plaintext = json.dumps(self.data)
        plaintext_length = str(len(plaintext))+'_'
        ciphertext = self._encrypt_message(plaintext)

        ciphertext_length = str(len(ciphertext))+'_'

        try:
            print("Sending data to eval_server")
            self.socket.sendall(ciphertext_length.encode("utf-8"))
            self.socket.sendall(ciphertext)
        except OSError:
            print("connection between eval_server and eval_client lost")
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
                print('no more data from the server')
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
                print('no more data from the server')
                self.stop()
            msg = data.decode("utf8")  # Decode raw bytes to UTF-8

            print("Message received from eval_server: ")
            print(msg)
            self.data = json.loads(msg)
            print(self.gamestate_queue.qsize())

        except ConnectionResetError:
            print('Connection Reset')
            self.stop()

        return

    def run(self):

        self.socket.connect(self.server_address)
        print("eval_client is now connected to eval_server!")
        while True:
            self.send_data()
            self.receive_data()
            self.gamestate_queue.put(self.data)
            time.sleep(5)

""""
def main():
    ip_addr = '192.168.95.226'
    port_num = 8080
    group_id = 'B03'
    secret_key = 1212121212121212
    default_game_state = {
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
    current_eval = eval_client(ip_addr, port_num, group_id, secret_key, default_game_state)

    current_eval.start()


if __name__ == '__main__':
    main()
"""