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
from player_new import player_new



class eval_client(threading.Thread):

    def __init__(self
                 , ip_addr
                 , port_num
                 , group_id
                 , secret_key
                 , game_mode
                 , default_game_state
                 , gamestate_queue
                 , prediction_queue):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (ip_addr, port_num)
        self.secret_key = secret_key
        # Game Mode: 0 - Single_Person. 1 - Two_Person. 2 - No_Eval_Server
        self.game_mode = game_mode
        self.predicted_gamestate = default_game_state
        self.gamestate_queue = gamestate_queue
        self.prediction_queue = prediction_queue
        self.p1_received = False
        self.p2_received = False
        self.p1 = player_new()
        self.p2 = player_new()

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
            #print("no_update")
            return "no_update"

    
    def play_game(self, sender, receiver, command):

        # Bullet fired and hit
        if command == 5:
            if ((sender == 1) and (receiver == 2)):
                self.p1.perform_shoot()
                if (self.predicted_gamestate["p1"]["bullets"] > 0):
                    self.p2.bullet_hit()
                else:
                    self.p2.no_apply()

            elif ((sender == 2) and (receiver == 1)):
                if (self.predicted_gamestate["p2"]["bullets"] > 0):
                    self.p1.bullet_hit()
                else:
                    self.p1.no_apply()
                self.p2.perform_shoot()

        # Grenade
        elif command == 1:
            if ((sender == 1) and (receiver == 2)):
                self.p1.perform_grenade()
                if (self.predicted_gamestate["p1"]["grenades"] > 0):
                    self.p2.grenade_hit()
                else:
                    self.p2.no_apply()
            elif ((sender == 2) and (receiver == 1)):
                if (self.predicted_gamestate["p2"]["grenades"] > 0):
                    self.p1.grenade_hit()
                else:
                    self.p1.no_apply()
                self.p2.perform_grenade()
        
        # Shield
        elif command == 3:
            if ((sender == 1) and (receiver == 2)):
                self.p1.perform_shield()
                self.p2.no_apply()
            elif ((sender == 2) and (receiver == 1)):
                self.p1.no_apply()
                self.p2.perform_shield()

        # Reload
        elif command == 2:
            if ((sender == 1) and (receiver == 2)):
                self.p1.perform_reload()
                self.p2.no_apply()
            elif ((sender == 2) and (receiver == 1)):
                self.p1.no_apply()
                self.p2.perform_reload()

        # Bullet Fired, but missed
        if command == 6:
            if ((sender == 1) and (receiver == 2)):
                self.p1.perform_shoot()
                self.p2.no_apply()

            elif ((sender == 2) and (receiver == 1)):
                self.p2.perform_shoot()
                self.p1.no_apply()

        # Logout
        if command == 0:
            if ((sender == 1) and (receiver == 2)):
                self.p1.perform_logout()
                self.p2.no_apply()

            elif ((sender == 2) and (receiver == 1)):
                self.p2.perform_logout()
                self.p1.no_apply()

        return
    
    def handle_gamestate(self):
        sender = self.prediction_value["sender"]
        receiver = self.prediction_value["receiver"]
        command = self.prediction_value["command"]

        self.p1.update_shield_timings()
        self.p2.update_shield_timings()

        self.play_game(sender, receiver, command)
        print("Gamestate calculated!")

        self.predicted_gamestate = {"p1": self.p1.get_dict(), "p2": self.p2.get_dict()}

        return
    
    def prediction_filter(self, AI_prediction):
        sender = AI_prediction["sender"]
        receiver = AI_prediction["receiver"]

        if (sender == 1) and (receiver == 2):
            if self.p1_received == False:
                self.p1_received = True
                return True
            elif self.p1_received == True:
                return False
                
        elif (sender == 2) and (receiver == 1):
            if self.p2_received == False:
                self.p2_received = True
                return True
            elif self.p2_received == True:
                return False
            


    def run(self):
        # Connect to Ultra96
        self.socket.connect(self.server_address)
        print("eval_client is now connected to eval_server!")

        while True:
            if self.game_mode != 2:
                updated_gamestate = self.receive_data()
                if updated_gamestate != "no_update":

                    # First, update the individual player states, then send evaluated gamestate to relay_server
                    self.p1.update_from_eval(updated_gamestate["p1"])
                    self.p2.update_from_eval(updated_gamestate["p2"])
                    self.predicted_gamestate = {"p1": self.p1.get_dict(), "p2": self.p2.get_dict()}
                    self.gamestate_queue.put(self.predicted_gamestate)
                    time.sleep(0)

                    # Try and obtain predicted gamestate from Hardware AI
                    try: 
                        AI_prediction = self.prediction_queue.get_nowait()
                        
                        is_valid_prediction = self.prediction_filter(AI_prediction)

                        if is_valid_prediction == True:
                            self.prediction_value = AI_prediction
                            self.handle_gamestate()
                            print("P1 Received: " + str(self.p1_received))
                            print("P2 Received: " + str(self.p2_received))

                        if (self.p1_received == True) and (self.p2_received == True):
                            self.send_data()
                            self.p1_received = False
                            self.p2_received = False
                        """
                        self.prediction_value = AI_prediction
                        self.handle_gamestate()
                        self.send_data()
                        """
                        time.sleep(0)

                    except Empty:
                        time.sleep(0)
                        continue

                elif updated_gamestate == "no_update":

                    # Try and obtain predicted gamestate from Hardware AI
                    try: 
                        AI_prediction = self.prediction_queue.get_nowait()
                        
                        valid_prediction = self.prediction_filter(AI_prediction)

                        if valid_prediction:
                            self.prediction_value = AI_prediction
                            self.handle_gamestate()
                            print("P1 Received: " + str(self.p1_received))
                            print("P2 Received: " + str(self.p2_received))

                        if (self.p1_received == True) and (self.p2_received == True):
                            self.send_data()
                            self.p1_received = False
                            self.p2_received = False
                        """
                        self.prediction_value = AI_prediction
                        self.handle_gamestate()
                        self.send_data()
                        """
                        time.sleep(0)

                    except Empty:
                        time.sleep(0)
                        continue

            elif self.game_mode == 2:
                try: 
                    self.prediction_value = self.prediction_queue.get_nowait()
                    self.handle_gamestate()
                    self.gamestate_queue.put(self.predicted_gamestate)
                    time.sleep(0)
                except Empty:
                    time.sleep(0)
                    continue



