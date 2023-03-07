import json
import pandas as pd
import os
import sys
import random as random
import time
import tkinter as tk
import threading
import traceback
from multiprocessing import Queue
from multiprocessing import Pipe

import datetime
from queue import Empty

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

        self.prediction = "none"
        self.dataframe = None
        self.accelerometer_queue = accelerometer_queue
        self.prediction_queue = prediction_queue
        threading.Thread.__init__(self)

        return
    
    def predict(self):
        # Placeholder
        dummy_prediction = input("Enter Dummy Prediction from eval_server: ")
        self.prediction = {"sender": "p1", "receiver": "p2", "command": dummy_prediction}

    
    def run(self):

        while True:
            self.dataframe = self.accelerometer_queue.get()
            print("From Hardware AI: Accerometer Data received!")
            self.predict()
            self.prediction_queue.put(self.prediction)
            print("From Hardware AI: Prediction Sent to eval_client!")

"""
