mport json
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
import ultra96_cnn as u96
# from ultra96_cnn import set_up_fpga
# from ultra96_cnn import run_inference

from datetime import datetime
from queue import Empty

class HardwareAI(threading.Thread):

    def __init__(self, accelerometer_queue, prediction_queue, cnn, sender, receiver):

        self.accelerometer_queue = accelerometer_queue
        self.prediction_queue = prediction_queue
        self.sender = sender
        self.receiver = receiver
        self.p1_shot_detect_time = 0
        self.p2_shot_detect_time = 0
        self.cnn = cnn
        threading.Thread.__init__(self)

    """
    def run(self):
        while True:
            prediction = input("Enter dummy input for Player {player_number}: ".format(player_number=self.sender))
            self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": int(prediction)})
            time.sleep(0)
    """

    def run(self):
        user_0_prediction = -1
        user_1_prediction = -1
        #prediction = -1
        while True:
            msg = self.accelerometer_queue.get()
            user = msg["player_id"] - 1
            #print(user)
            #print(msg["player_id"])
            #print(msg)
            msg_array = np.array(
                [msg["acc_x"], msg["acc_y"], msg["acc_z"], msg["gyro_x"], msg["gyro_y"], msg["gyro_z"]])
            if (msg["message_type"] == 6):
                if ((msg["acc_x"] == 0) and (msg["acc_y"] == 0) and (msg["acc_z"] == 0)
                        and (msg["gyro_x"] == 0) and (msg["gyro_y"] == 0) and (msg["gyro_z"] == 0)):
                    user_0_prediction = -1
                    user_1_prediction = -1
                    u96.reset_model(self.cnn, user)
                else:
                    if user == 0 and user_0_prediction == -1:
                        user_0_prediction = u96.run_inference(self.cnn, msg_array, user)
                        if user_0_prediction != -1:
                            self.sender = 1
                            self.receiver = 2
                            self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": user_0_prediction})
                            print(user_0_prediction)
                    if user == 1 and user_1_prediction == -1:
                        user_1_prediction = u96.run_inference(self.cnn, msg_array, user)
                        if user_1_prediction != -1:
                            self.sender = 2
                            self.receiver = 1
                            self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": user_1_prediction})
                            print(user_1_prediction)

            elif (msg["message_type"] == 4):
                print("Read from accelerometer queue at : " + str(
                    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))

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
            time.sleep(0)



            

