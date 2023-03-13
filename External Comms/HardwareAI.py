import json
import pandas as pd
import numpy as np
import os
import sys
import random as random
import time
import tkinter as tk
import threading
import traceback
from multiprocessing import Queue
from multiprocessing import Pipe
import random

from timeit import default_timer as timer
import time

# from ultra96_cnn import set_up_fpga
# from ultra96_cnn import run_inference

from datetime import datetime
from queue import Empty

"""
class HardwareAI(threading.Thread):

    def __init__(self, AI_to_relay_conn, AI_to_eval_conn):

        self.prediction = "none"
        self.dataframe = None
        self.AI_to_relay_conn = AI_to_relay_conn
        self.AI_to_eval_conn = AI_to_eval_conn
        threading.Thread.__init__(self)

        return
    
    def predict(self):
        # Placeholder
        dummy_prediction = input("Enter Dummy Prediction from eval_server: ")
        self.prediction = {"sender": "p1", "receiver": "p2", "command": dummy_prediction}

    
    def run(self):

        while True:
            self.dataframe = self.AI_to_relay_conn.recv()
            print("From Hardware AI: Accerometer Data received!")
            self.predict()
            self.AI_to_eval_conn.send(self.prediction)
            print("From Hardware AI: Prediction Sent to eval_client!")
"""

class HardwareAI(threading.Thread):

    def __init__(self, accelerometer_queue, prediction_queue):

        self.accelerometer_queue = accelerometer_queue
        self.prediction_queue = prediction_queue
        self.sender = 0
        self.debug_relay = 0
        self.receiver = 0
        self.p1_shot_detect_time = 0
        self.p2_shot_detect_time = 0
        self.msg = {"acc_x": 1, "acc_y": 1, "acc_z": 1, "gyro_x": 1, "gyro_y": 1, "gyro_z": 1}

        threading.Thread.__init__(self)

    """
    def run(self):
        while True:
            prediction = input("Enter dummy input: ")
            self.prediction_queue.put({"sender": 1, "receiver": 2, "command": int(prediction)})
    """

    
    def run(self):

        # cnn = set_up_fpga()

        while True:
            # self.dataframe = self.accelerometer_queue.get()
            # msg = self.msg
            msg = self.accelerometer_queue.get()
            msg_array = np.array([msg["acc_x"], msg["acc_y"], msg["acc_z"], msg["gyro_x"], msg["gyro_y"], msg["gyro_z"]])

            
            if (msg["message_type"] == 6):
                start_time = timer()
                #prediction = run_inference(cnn, msg_array)
                prediction = -1
                end_time = timer()
                if (prediction == -1):
                    continue
                else:
                    if msg["player_id"] == 1:
                        self.sender = 1
                        self.receiver = 2
                    elif msg["player_id"] == 2:
                        self.sender = 2
                        self.receiver = 1
                    self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": prediction})
                    print(end_time - start_time)
                    print(prediction)
            
                    
            
            elif (msg["message_type"] == 4):
                print("Read from accelerometer queue at : " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))

                if msg["player_id"] == 1:
                    self.sender = 1
                    self.receiver = 2
                    self.p1_shot_detect_time = time.time()
                    print("Player 1 Shot Sent at " + str(self.p1_shot_detect_time))
                    self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": 5})
                elif msg["player_id"] == 2:
                    self.sender = 2
                    self.receiver = 1
                    self.p2_shot_detect_time = time.time()
                    print("Player 2 Shot Sent at " + str(self.p2_shot_detect_time))
                    self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": 5})

            """
            elif (msg["message_type"] == 5):
                if msg["player_id"] == 1:
                    self.sender = 2
                    self.receiver = 1
                    current_time = timer()
                    print("Player 1 Shot Received at " + str(current_time))

                    self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": 5})
                    
                    if current_time - self.p2_shot_detect_time < 1:
                        self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": 5})
                    else:
                        self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": 6})
                    

                elif msg["player_id"] == 2:
                    self.sender = 1
                    self.receiver = 2
                    current_time = timer()
                    print("Player 2 Shot Received at " + str(current_time))

                    if current_time - self.p1_shot_detect_time < 1:
                        print("HOHO")
                        self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": 5})
                    else:
                        self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": 6})
            """


