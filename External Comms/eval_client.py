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
from queue import Empty

from player import player


class eval_client(threading.Thread):

    def __init__(self
                 , ip_addr
                 , port_num
                 , group_id
                 , secret_key
                 , game_mode
                 , gamestate_queue
                 , prediction_queue
                 , p1_queue
                 , p2_queue):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (ip_addr, port_num)
        self.secret_key = secret_key
        # Game Mode: 0 - Single_Person. 1 - Two_Person. 2 - No_Eval_Server
        self.game_mode = game_mode
        self.predicted_gamestate = None
        self.gamestate_queue = gamestate_queue
        self.prediction_queue = prediction_queue
        self.p1_queue = p1_queue
        self.p2_queue = p2_queue
        self.p1 = player(p1_queue)
        self.p2 = player(p2_queue)

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
        
        plaintext = json.dumps(self.predicted_gamestate)
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

            correct_gamestate = json.loads(msg)
            self.gamestate_queue.put(correct_gamestate)

        except ConnectionResetError:
            print('Connection Reset')
            self.stop()

        return
    
    def singleperson_game(self, sender, command):

        if command == "shoot":
            if sender == "p1":
                self.p1_queue.put("perform_shoot")
                time.sleep(1)
            elif (sender == "p2"):
                self.p2_queue.put("perform_shoot")
                time.sleep(1)

        elif command == "grenade":
            if (sender == "p1"):
                self.p1_queue.put("perform_grenade")
                time.sleep(1)
            elif (sender == "p2"):
                self.p2_queue.put("perform_grenade")
                time.sleep(1)
        
        elif command == "shield":
            if (sender == "p1"):
                self.p1_queue.put("perform_shield")
                time.sleep(1)
            elif (sender == "p2"):
                self.p2_queue.put("perform_shield")
                time.sleep(1)

        elif command == "reload":
            if (sender == "p1"):
                self.p1_queue.put("perform_reload")
                time.sleep(1)
            elif (sender == "p2"):
                self.p2_queue.put("perform_reload")
                time.sleep(1)

        return

    
    def multiperson_game(self, sender, receiver, command):

        if command == "shoot":
            if ((sender == "p1") and (receiver == "p2")):
                self.p1_queue.put("perform_shoot")
                self.p2_queue.put("bullet_hit")
                time.sleep(1)
            elif ((sender == "p2") and (receiver == "p1")):
                self.p1_queue.put("bullet_hit")
                self.p2_queue.put("perform_shoot")
                time.sleep(1)

        elif command == "grenade":
            if ((sender == "p1") and (receiver == "p2")):
                self.p1_queue.put("perform_grenade")
                self.p2_queue.put("grenade_hit")
                time.sleep(1)
            elif ((sender == "p2") and (receiver == "p1")):
                self.p1_queue.put("grenade_hit")
                self.p2_queue.put("perform_grenade")
                time.sleep(1)
        
        elif command == "shield":
            if ((sender == "p1") and (receiver == "p2")):
                self.p1_queue.put("perform_shield")
                time.sleep(1)
            elif ((sender == "p2") and (receiver == "p1")):
                self.p2_queue.put("perform_shield")
                time.sleep(1)

        elif command == "reload":
            if ((sender == "p1") and (receiver == "p2")):
                self.p1_queue.put("perform_reload")
                time.sleep(1)
            elif ((sender == "p2") and (receiver == "p1")):
                self.p2_queue.put("perform_reload")
                time.sleep(1)

        return
    
    def handle_gamestate(self):
        sender = self.prediction_value["sender"]
        receiver = self.prediction_value["receiver"]
        command = self.prediction_value["command"]

        if self.game_mode == 0:
            self.singleperson_game(sender, command)
        elif self.game_mode != 0:
            self.multiperson_game(sender, receiver, command)
        
        self.predicted_gamestate = {"p1": self.p1.playerstate, "p2": self.p2.playerstate}


    def run(self):
        # Connect to Ultra96
        self.socket.connect(self.server_address)
        print("eval_client is now connected to eval_server!")

        # Start the 2 players
        self.p1.start()
        self.p2.start()

        while True:
            try: 
                self.prediction_value = self.prediction_queue.get()
                print("Handling Gamestate")
                self.handle_gamestate()
                if self.game_mode != 2:
                    self.send_data()
                    self.receive_data()
                elif self.game_mode == 2:
                    self.gamestate_queue.put(self.predicted_gamestate)
            except Empty:
                continue
        
        self.p1.join()
        self.p2.join()




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