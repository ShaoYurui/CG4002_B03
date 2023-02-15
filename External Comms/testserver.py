import socket
import sys
import threading
import time
from queue import Queue

import os
import subprocess

s = socket.socket()
host = '127.0.0.1'
port = 2030

s.connect((host, port))

while True:
    data = s.recv(1024)
    print(data.decode("utf-8"))
    message = "Ack Client 2"
    s.send(message.encode("utf-8"))