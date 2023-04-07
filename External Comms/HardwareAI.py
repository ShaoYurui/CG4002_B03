import json
import pandas as pd
import numpy as np
import os
import sys
import random as random
import time
import threading
import traceback
from multiprocessing import Queue
from multiprocessing import Pipe
import random

from my_timer import my_timer
import time
#import ultra96_cnn as u96

from datetime import datetime
from queue import Empty

#class HardwareAI(threading.Thread):
class HardwareAI():

    def __init__(self, accelerometer_queue, prediction_queue, cnn, sender, receiver):

        self.accelerometer_queue = accelerometer_queue
        self.prediction_queue = prediction_queue
        self.sender = sender
        self.receiver = receiver
        self.fire_shot_flag = False
        self.got_shot_flag = False
        self.cnn = cnn
        self.my_timer = my_timer()
        #threading.Thread.__init__(self)

    
    def run(self):
        while True:
            prediction = input("Enter dummy input for Player {player_number}: ".format(player_number=self.sender))
            self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": int(prediction)})
            #time.sleep(0)
    """

    def run(self):
        user_0_prediction = -1
        user_1_prediction = -1
        while True:
            msg = self.accelerometer_queue.get()
            user = msg["player_id"] - 1
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
                        if user_0_prediction == 0:
                            #print("User 1 Walking Detected")
                            user_0_prediction = -1
                        if user_0_prediction != -1:
                            self.sender = 1
                            self.receiver = 2
                            self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": user_0_prediction})
                            print(user_0_prediction)
                    if user == 1 and user_1_prediction == -1:
                        user_1_prediction = u96.run_inference(self.cnn, msg_array, user)
                        if user_1_prediction == 0:
                            #print("User 2 Walking Detected")
                            user_1_prediction = -1
                        if user_1_prediction != -1:
                            self.sender = 2
                            self.receiver = 1
                            self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": user_1_prediction})
                            print(user_1_prediction)

            elif (msg["message_type"] == 4):
                #print("Shots detected by Hardware AI at : " + str(
                #    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))

                self.fire_shot_flag = True

            elif (msg["message_type"] == 5):
                #print("Vest detected by Hardware AI at : " + str(
                #    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))

                self.got_shot_flag = True

            #if (self.sender == 2):
             #   print(self.my_timer.get_timer())

            if self.fire_shot_flag == True and (self.my_timer.get_timer() == -1):
                self.my_timer.start_timer()

            if (self.my_timer.get_timer() > 0.5) and (self.got_shot_flag == False) and (self.fire_shot_flag == True):
                self.my_timer.stop_timer()
                self.got_shot_flag = False
                self.fire_shot_flag = False
                self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": 6})
                print("Shot fired by player {player} is not successful.".format(player=self.sender))

            if (self.my_timer.get_timer() > 0) and (self.my_timer.get_timer() < 0.5) and (self.got_shot_flag == True) and (self.fire_shot_flag == True):
                self.my_timer.stop_timer()
                self.got_shot_flag = False
                self.fire_shot_flag = False
                self.prediction_queue.put({"sender": self.sender, "receiver": self.receiver, "command": 5})
                print("Shot fired by player {player} is successful.".format(player=self.sender))


            #time.sleep(0)
    """
        


            

