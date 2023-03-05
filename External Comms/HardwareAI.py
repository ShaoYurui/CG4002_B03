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

import datetime
from queue import Empty

class HardwareAI(threading.Thread):

    def __init__(self, accelerometer_queue, prediction_queue):

        self.dataframe = None
        self.prediction = "none"
        self.accelerometer_queue = accelerometer_queue
        self.prediction_queue = prediction_queue
        threading.Thread.__init__(self)

        return
    
    def predict(self):
        # Placeholder
        self.prediction = input("Enter Dummy Prediction from eval_server: ")
    
    def run(self):

        while True:
            
            endTime = datetime.datetime.now() + datetime.timedelta(microseconds=2560)
            while datetime.datetime.now() <= endTime:
                try:
                    msg = self.accelerometer_queue.get()
                except Empty:
                    continue
            
            empty_df = pd.DataFrame(columns=["player_id", "x_data", "y_data", "z_data"])
            msg_df = pd.DataFrame([msg])
            self.dataframe = pd.concat([msg_df, empty_df], ignore_index=True)
            
            self.predict()
            self.prediction_queue.put(self.prediction)



            

        
