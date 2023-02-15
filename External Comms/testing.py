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
from Crypto.Util.Padding import unpad
from Crypto import Random
import traceback
from queue import Queue

import GameState

class Testing:

    def __init__(self, game_state):

        self.game_state = game_state