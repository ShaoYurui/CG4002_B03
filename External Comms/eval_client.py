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
from multiprocessing import Pipe
from queue import Empty

"""
class eval_client(threading.Thread):

    def __init__(self
                 , ip_addr
                 , port_num
                 , group_id
                 , secret_key
                 , game_mode
                 , eval_to_relay_conn
                 , eval_to_AI_conn
                 , eval_to_p1_conn
                 , eval_to_p2_conn):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (ip_addr, port_num)
        self.secret_key = secret_key
        # Game Mode: 0 - Single_Person. 1 - Two_Person. 2 - No_Eval_Server
        self.game_mode = game_mode
        self.predicted_gamestate = None
        self.eval_to_relay_conn = eval_to_relay_conn
        self.eval_to_AI_conn = eval_to_AI_conn
        self.eval_to_p1_conn = eval_to_p1_conn
        self.eval_to_p2_conn = eval_to_p2_conn

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
            return correct_gamestate

        except ConnectionResetError:
            print('Connection Reset')
            self.stop()

        return
    
    def singleperson_game(self, sender, command):

        if command == "shoot":
            if sender == "p1":
                self.eval_to_p1_conn.send("perform_shoot")
            elif (sender == "p2"):
                self.eval_to_p2_conn.send("perform_shoot")

        elif command == "grenade":
            if (sender == "p1"):
                self.eval_to_p1_conn.send("perform_grenade")
            elif (sender == "p2"):
                self.eval_to_p2_conn.send("perform_grenade")
                    
        elif command == "shield":
            if (sender == "p1"):
                self.eval_to_p1_conn.send("perform_shield")
            elif (sender == "p2"):
                self.eval_to_p2_conn.send("perform_shield")

        elif command == "reload":
            if (sender == "p1"):
                self.eval_to_p1_conn.send("perform_reload")
            elif (sender == "p2"):
                self.eval_to_p2_conn.send("perform_reload")
        
        print("From eval_client: Prediction sent to players")

        return

    
    def multiperson_game(self, sender, receiver, command):

        if command == "shoot":
            if ((sender == "p1") and (receiver == "p2")):
                self.eval_to_p1_conn.send("perform_shoot")
                self.eval_to_p2_conn.send("bullet_hit")
            elif ((sender == "p2") and (receiver == "p1")):
                self.eval_to_p1_conn.send("bullet_hit")
                self.eval_to_p2_conn.send("perform_shoot")

        elif command == "grenade":
            if ((sender == "p1") and (receiver == "p2")):
                self.eval_to_p1_conn.send("perform_grenade")
                self.eval_to_p2_conn.send("grenade_hit")
            elif ((sender == "p2") and (receiver == "p1")):
                self.eval_to_p1_conn.send("grenade_hit")
                self.eval_to_p2_conn.send("perform_grenade")
        
        elif command == "shield":
            if ((sender == "p1") and (receiver == "p2")):
                self.eval_to_p1_conn.send("perform_shield")
            elif ((sender == "p2") and (receiver == "p1")):
                self.eval_to_p2_conn.send("perform_shield")

        elif command == "reload":
            if ((sender == "p1") and (receiver == "p2")):
                self.eval_to_p1_conn.send("perform_reload")
            elif ((sender == "p2") and (receiver == "p1")):
                self.eval_to_p2_conn.send("perform_reload")

        print("From eval_client: Prediction sent to players")

        return
    
    def handle_gamestate(self):
        sender = self.prediction_value["sender"]
        receiver = self.prediction_value["receiver"]
        command = self.prediction_value["command"]

        if self.game_mode == 0:
            self.singleperson_game(sender, command)
            print("HOHOHOHO!")
            p1_playerstate = self.eval_to_p1_conn.recv()
            print("Hi!")
            p2_playerstate = {
                                "hp": 100,
                                "action": "none",
                                "bullets": 6,
                                "grenades": 2,
                                "shield_time": 10,
                                "shield_health": 30,
                                "num_deaths": 0,
                                "num_shield": 3
                                }
            
        elif self.game_mode != 0:
            self.multiperson_game(sender, receiver, command)
            p1_playerstate = self.eval_to_p1_conn.recv()
            print("From eval_client: Player 1 Gamestate calculated")
            p2_playerstate = self.eval_to_p2_conn.recv()
            print("From eval_client: Player 2 Gamestate calculated")
        self.predicted_gamestate = {"p1": p1_playerstate, "p2": p2_playerstate}
        print(self.predicted_gamestate["p1"])


    def run(self):
        # Connect to Ultra96
        self.socket.connect(self.server_address)
        print("eval_client is now connected to eval_server!")

        while True:
            try: 
                self.prediction_value = self.eval_to_AI_conn.recv()
                print("From eval_client: Prediction Obtained!")

                self.handle_gamestate()

                if self.game_mode != 2:
                    self.send_data()
                    updated_gamestate = self.receive_data()
                elif self.game_mode == 2:
                    updated_gamestate = self.predicted_gamestate
                
                self.eval_to_relay_conn.send(updated_gamestate)

            except Empty:
                continue
"""


class eval_client(threading.Thread):

    def __init__(self
                 , ip_addr
                 , port_num
                 , group_id
                 , secret_key
                 , game_mode
                 , gamestate_queue_1
                 , gamestate_queue_2
                 , prediction_queue
                 , eval_to_p1_queue
                 , eval_to_p2_queue
                 , p1_to_eval_queue
                 , p2_to_eval_queue):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (ip_addr, port_num)
        self.secret_key = secret_key
        # Game Mode: 0 - Single_Person. 1 - Two_Person. 2 - No_Eval_Server
        self.game_mode = game_mode
        self.predicted_gamestate = None
        self.gamestate_queue_1 = gamestate_queue_1
        self.gamestate_queue_2 = gamestate_queue_2
        self.prediction_queue = prediction_queue
        self.eval_to_p1_queue = eval_to_p1_queue
        self.eval_to_p2_queue = eval_to_p2_queue
        self.p1_to_eval_queue = p1_to_eval_queue
        self.p2_to_eval_queue = p2_to_eval_queue

        threading.Thread.__init__(self)
    

    def _encrypt_message(self, plaintext):
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
            return correct_gamestate

        except ConnectionResetError:
            print('Connection Reset')
            self.stop()

        return
    
    def singleperson_game(self, sender, command):

        if command == "shoot":
            if sender == "p1":
                self.eval_to_p1_queue.put("perform_shoot")
                self.eval_to_p2_queue.put("bullet_hit")

            elif (sender == "p2"):
                self.eval_to_p1_queue.put("bullet_hit")
                self.eval_to_p2_queue.put("perform_shoot")

        elif command == "grenade":
            if (sender == "p1"):
                self.eval_to_p1_queue.put("perform_grenade")
                self.eval_to_p2_queue.put("grenade_hit")
            elif (sender == "p2"):
                self.eval_to_p1_queue.put("grenade_hit")
                self.eval_to_p2_queue.put("perform_grenade")
                    
        elif command == "shield":
            if (sender == "p1"):
                self.eval_to_p1_queue.put("perform_shield")
                self.eval_to_p2_queue.put("no_apply")
            elif (sender == "p2"):
                self.eval_to_p1_queue.put("no_apply")
                self.eval_to_p2_queue.put("perform_shield")

        elif command == "reload":
            if (sender == "p1"):
                self.eval_to_p1_queue.put("perform_reload")
                self.eval_to_p2_queue.put("no_apply")
            elif (sender == "p2"):
                self.eval_to_p1_queue.put("no_apply")
                self.eval_to_p2_queue.put("perform_reload")
        
        return

    
    def multiperson_game(self, sender, receiver, command):

        if command == "shoot":
            if ((sender == "p1") and (receiver == "p2")):
                self.eval_to_p1_queue.put("perform_shoot")
                self.eval_to_p2_queue.put("bullet_hit")
            elif ((sender == "p2") and (receiver == "p1")):
                self.eval_to_p1_queue.put("bullet_hit")
                self.eval_to_p2_queue.put("perform_shoot")

        elif command == "grenade":
            if ((sender == "p1") and (receiver == "p2")):
                self.eval_to_p1_queue.put("perform_grenade")
                self.eval_to_p2_queue.put("grenade_hit")
            elif ((sender == "p2") and (receiver == "p1")):
                self.eval_to_p1_queue.put("grenade_hit")
                self.eval_to_p2_queue.put("perform_grenade")
        
        elif command == "shield":
            if ((sender == "p1") and (receiver == "p2")):
                self.eval_to_p1_queue.put("perform_shield")
                self.eval_to_p2_queue.put("no_apply")
            elif ((sender == "p2") and (receiver == "p1")):
                self.eval_to_p1_queue.put("no_apply")
                self.eval_to_p2_queue.put("perform_shield")

        elif command == "reload":
            if ((sender == "p1") and (receiver == "p2")):
                self.eval_to_p1_queue.put("perform_reload")
                self.eval_to_p2_queue.put("no_apply")
            elif ((sender == "p2") and (receiver == "p1")):
                self.eval_to_p1_queue.put("no_apply")
                self.eval_to_p2_queue.put("perform_reload")

        return
    
    def handle_gamestate(self):
        sender = self.prediction_value["sender"]
        receiver = self.prediction_value["receiver"]
        command = self.prediction_value["command"]

        if self.game_mode == 0:
            self.singleperson_game(sender, command)
            
        elif self.game_mode != 0:
            self.multiperson_game(sender, receiver, command)

        p1_playerstate = self.p1_to_eval_queue.get()
        p2_playerstate = self.p2_to_eval_queue.get()
        self.predicted_gamestate = {"p1": p1_playerstate, "p2": p2_playerstate}

        return


    def run(self):
        # Connect to Ultra96
        self.socket.connect(self.server_address)
        print("eval_client is now connected to eval_server!")

        while True:
            try: 
                self.prediction_value = self.prediction_queue.get()
                print("From eval_client: Prediction Obtained!")

                self.handle_gamestate()

                if self.game_mode != 2:
                    self.send_data()
                    updated_gamestate = self.receive_data()
                elif self.game_mode == 2:
                    updated_gamestate = self.predicted_gamestate
                
                self.gamestate_queue_1.put(updated_gamestate)
                self.gamestate_queue_2.put(updated_gamestate)

            except Empty:
                continue


"""
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