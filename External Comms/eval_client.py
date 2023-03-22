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
from datetime import datetime



class eval_client(threading.Thread):

    def __init__(self
                 , ip_addr
                 , port_num
                 , group_id
                 , secret_key
                 , game_mode
                 , default_game_state
                 , gamestate_queue
                 , prediction_queue
                 , eval_to_p1_queue
                 , eval_to_p2_queue
                 , p1_to_eval_queue
                 , p2_to_eval_queue
                 , eval_to_p1_update_queue
                 , eval_to_p2_update_queue):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (ip_addr, port_num)
        self.secret_key = secret_key
        # Game Mode: 0 - Single_Person. 1 - Two_Person. 2 - No_Eval_Server
        self.game_mode = game_mode
        self.predicted_gamestate = default_game_state
        self.gamestate_queue = gamestate_queue
        self.prediction_queue = prediction_queue
        self.eval_to_p1_queue = eval_to_p1_queue
        self.eval_to_p2_queue = eval_to_p2_queue
        self.p1_to_eval_queue = p1_to_eval_queue
        self.p2_to_eval_queue = p2_to_eval_queue
        self.eval_to_p1_update_queue = eval_to_p1_update_queue
        self.eval_to_p2_update_queue = eval_to_p2_update_queue

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
        self.socket.setblocking(0)
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
            self.socket.setblocking(1)

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
            self.socket.setblocking(0)
            return correct_gamestate

        except ConnectionResetError:
            print('Connection Reset')
            sys.exit()

        except BlockingIOError:
            return "no_update"

    
    def play_game(self, sender, receiver, command):

        # Bullet fired and hit
        if command == 5:
            if ((sender == 1) and (receiver == 2)):
                self.eval_to_p1_queue.put("perform_shoot")
                if (self.predicted_gamestate["p1"]["bullets"] > 0):
                    self.eval_to_p2_queue.put("bullet_hit")
                else:
                    self.eval_to_p2_queue.put("no_apply")


            elif ((sender == 2) and (receiver == 1)):
                if (self.predicted_gamestate["p2"]["bullets"] > 0):
                    self.eval_to_p1_queue.put("bullet_hit")
                else:
                    self.eval_to_p1_queue.v("no_apply")
                self.eval_to_p2_queue.put("perform_shoot")

        # Grenade
        elif command == 1:
            if ((sender == 1) and (receiver == 2)):
                self.eval_to_p1_queue.put("perform_grenade")
                if (self.predicted_gamestate["p1"]["grenades"] > 0):
                    self.eval_to_p2_queue.put("grenade_hit")
                else:
                    self.eval_to_p2_queue.put("no_apply")
            elif ((sender == 2) and (receiver == 1)):
                if (self.predicted_gamestate["p2"]["grenades"] > 0):
                    self.eval_to_p1_queue.put("grenade_hit")
                else:
                    self.eval_to_p1_queue.put("no_apply")
                self.eval_to_p2_queue.put("perform_grenade")
        
        # Shield
        elif command == 3:
            if ((sender == 1) and (receiver == 2)):
                self.eval_to_p1_queue.put("perform_shield")
                self.eval_to_p2_queue.put("no_apply")
            elif ((sender == 2) and (receiver == 1)):
                self.eval_to_p1_queue.put("no_apply")
                self.eval_to_p2_queue.put("perform_shield")

        # Reload
        elif command == 2:
            if ((sender == 1) and (receiver == 2)):
                self.eval_to_p1_queue.put("perform_reload")
                self.eval_to_p2_queue.put("no_apply")
            elif ((sender == 2) and (receiver == 1)):
                self.eval_to_p1_queue.put("no_apply")
                self.eval_to_p2_queue.put("perform_reload")

        # Bullet Fired, but missed
        if command == 6:
            if ((sender == 1) and (receiver == 2)):
                self.eval_to_p1_queue.put("perform_shoot")
                self.eval_to_p2_queue.put("no_apply")

            elif ((sender == 2) and (receiver == 1)):
                self.eval_to_p2_queue.put("perform_shoot")
                self.eval_to_p1_queue.put("no_apply")

        return
    
    def handle_gamestate(self):
        sender = self.prediction_value["sender"]
        receiver = self.prediction_value["receiver"]
        command = self.prediction_value["command"]

        self.play_game(sender, receiver, command)
        print("Gamestate calculated!")

        p1_playerstate = self.p1_to_eval_queue.get()
        print("Player 1 Gamestate calculated at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
        p2_playerstate = self.p2_to_eval_queue.get()
        print("Player 2 Gamestate calculated at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))

        self.predicted_gamestate = {"p1": p1_playerstate, "p2": p2_playerstate}

        return


    def run(self):
        # Connect to Ultra96
        self.socket.connect(self.server_address)
        print("eval_client is now connected to eval_server!")

        while True:
            try:
                if self.game_mode != 2:
                    updated_gamestate = self.receive_data()
                    if updated_gamestate != "no_update":
                        self.predicted_gamestate = updated_gamestate

                        self.gamestate_queue.put(updated_gamestate)
                        self.eval_to_p1_update_queue.put(updated_gamestate["p1"])
                        self.eval_to_p2_update_queue.put(updated_gamestate["p2"])

                self.prediction_value = self.prediction_queue.get_nowait()

                self.handle_gamestate()

                """
                if ((self.predicted_gamestate["p1"] == "logout") and (self.predicted_gamestate["p2"] == "logout")):
                    self.gamestate_queue.put("logout")
                """

                if self.game_mode != 2:
                    self.send_data()
                    #updated_gamestate = self.receive_data()
                
                elif self.game_mode == 2:
                    updated_gamestate = self.predicted_gamestate
                    self.gamestate_queue.put(updated_gamestate)
                    self.eval_to_p1_update_queue.put(updated_gamestate["p1"])
                    self.eval_to_p2_update_queue.put(updated_gamestate["p2"])
                """
                # For checking for action validity
                if updated_gamestate != "no_update":
                    self.predicted_gamestate = updated_gamestate
                
                    self.gamestate_queue.put(updated_gamestate)
                    self.eval_to_p1_update_queue.put(updated_gamestate["p1"])
                    self.eval_to_p2_update_queue.put(updated_gamestate["p2"])
                """

            except Empty:
                """
                print("THROTTLED!")
                if self.game_mode != 2:
                    updated_gamestate = self.receive_data()
                    if updated_gamestate != "no_update":
                        self.predicted_gamestate = updated_gamestate
                        self.gamestate_queue.put(updated_gamestate)
                        self.eval_to_p1_update_queue.put(updated_gamestate["p1"])
                        self.eval_to_p2_update_queue.put(updated_gamestate["p2"])
                """
                continue
        """
        while True:
            try:
                self.prediction_value = self.prediction_queue.get()

                self.handle_gamestate()

                if ((self.predicted_gamestate["p1"] == "logout") and (self.predicted_gamestate["p2"] == "logout")):
                    self.gamestate_queue.put("logout")

                if self.game_mode != 2:
                    self.send_data()
                    updated_gamestate = self.receive_data()
                elif self.game_mode == 2:
                    updated_gamestate = self.predicted_gamestate
                
                # For checking for action validity
                self.predicted_gamestate = updated_gamestate

                self.gamestate_queue.put(updated_gamestate)
                self.eval_to_p1_queue.put(updated_gamestate["p1"])
                self.eval_to_p2_queue.put(updated_gamestate["p2"])

            except Empty:
                continue
        """


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