from bluepy import btle

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
import traceback
from multiprocessing import Queue
from queue import Empty

from datetime import datetime

import struct
import curses

PLAYER_ID = b'\x01' # \x01 or \x02

ACK = b'\x41'
NAK = b'\x4E'

REQUEST_H = b'\x48'
ACK_H = b'\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x40'

nBeetle = 3

mac = list()
if PLAYER_ID == b'\x01':
    mac.append('80:30:dc:d9:1f:93')  # gun x
    mac.append('34:15:13:22:a1:37')  # vest x
    #mac.append('80:30:dc:e9:1c:74')  # imu X
    mac.append('80:30:dc:e9:08:d7')  # imu # swapped for testing
elif PLAYER_ID == b'\x02':
    mac.append('34:14:b5:51:d9:04') # gun
    mac.append('80:30:dc:d9:23:27') # vest
    #mac.append('80:30:dc:e9:08:d7') # imu
    mac.append('80:30:dc:e9:1c:74')  # imu X # swapped for testing

d = list() #devices list
c = list() #connection to cloud


class PeripheralDevice(threading.Thread):
    def __init__(self, pid):
        self.pid = pid
        self.peripheral = btle.Peripheral()
        self.svc = 0
        self.ch = 0
        self.setup = False
        self.connection = False
        self.handshake_start = False
        self.handshake_done = False
        self.handshake_timeout = 0
        self.data = bytearray(b'')

        self.current_gun_state = 0
        self.current_vest_state = 0
        self.game_state_timeout = 0

        threading.Thread.__init__(self)

    def get_cs(self, inByte):
        cs = 0
        for i in range(8):
            cs ^= (inByte << i)
        cs &= 1
        return inByte | cs

    def setup_connection(self):
        print("Connecting device {id}".format(id=self.pid))
        try:
            self.peripheral.connect(mac[self.pid])
            self.connection = True
            self.peripheral.setDelegate(CommunicationDelegate(self.pid))
            self.svc = self.peripheral.getServiceByUUID('0000dfb0-0000-1000-8000-00805f9b34fb')
            self.ch = self.svc.getCharacteristics()[0]
            self.setup = True
            print("Device[{id}] connected".format(id=self.pid))
        except btle.BTLEDisconnectError:
            print("Device[{id}] not connected".format(id=self.pid))
        except AttributeError:
            print("Device[{id}] not connected".format(id=self.pid))
            time.sleep(1)

    def check_setup(self):
        if not self.setup:
            print("Try setting up device[{id}] again".format(id=self.pid))
            try:
                self.peripheral.connect(mac[self.pid])
                self.connection = True
                self.peripheral.setDelegate(CommunicationDelegate(self.pid))
                self.svc = self.peripheral.getServiceByUUID('0000dfb0-0000-1000-8000-00805f9b34fb')
                self.ch = self.svc.getCharacteristics()[0]
                self.setup = True
                self.handshake_start = False
                self.handshake_done = False
                print("Device[{id}] connected".format(id=self.pid))
                return
            except btle.BTLEDisconnectError:
                print("Device[{id}] still not connected".format(id=self.pid))
            except AttributeError:
                print("Device[{id}] not connected".format(id=self.pid))
                time.sleep(1)

    def check_connection(self):
        if self.setup and not self.connection:  # check connection
            print("Reconnecting device[{id}]".format(id=self.pid))
            try:
                self.peripheral.connect(mac[self.pid])
                self.connection = True
                self.handshake_start = False
                self.handshake_done = False
                print("Device[{id}] connected".format(id=self.pid))
            except btle.BTLEDisconnectError:
                self.connection = False
                print("Device[{id}] not connected".format(id=self.pid))

    def start_handshake(self):
        if self.connection and not self.handshake_start:  # check handshake has begun
            try:
                time.sleep(5)
                self.handshake_timeout = time.time() + 3  # 3s from now
                self.ch.write(REQUEST_H)
                self.handshake_start = True
                print("Device[{id}] begin handshake".format(id=self.pid))
            except btle.BTLEDisconnectError:
                print("Device[{id}] disconnected".format(id=self.pid))
                self.connection = False

    def check_handshake_finish(self):
        if self.connection and self.handshake_start and not self.handshake_done:  # check handshake ack
            print("Device[{id}] waiting handshake ACK...".format(id=self.pid))
            try:
                if self.peripheral.waitForNotifications(1.0):
                    print("Device[{id}] handshake ACK received".format(id=self.pid))
                    self.handshake_done = True
                    return
                elif time.time() > self.handshake_timeout:
                    print("Device[{id}] resend handshake".format(id=self.pid))
                    self.handshake_start = False
                    self.handshake_done = False
            except btle.BTLEDisconnectError:
                print("Device[{id}] disconnected".format(id=self.pid))
                self.connection = False

    def do_handshake(self):
        self.check_setup()
        self.start_handshake()
        self.check_handshake_finish()

    def send_data(self):
        try:
            if self.pid == 0:
                gun_data = c[0].data_to_gun.get_nowait()
                gun_data_b = gun_data.to_bytes(1, 'big')
                self.ch.write(gun_data_b)
                self.current_gun_state = gun_data_b
                self.game_state_timeout = time.time() + 1
                print("d[{i}] send data to gun: {bullets}".format(i=self.pid, bullets=gun_data))
            elif self.pid == 1:
                vest_data = c[0].data_to_vest.get_nowait()
                vest_data_b = vest_data.to_bytes(1, 'big')
                self.ch.write(vest_data_b)
                self.current_vest_state = vest_data_b
                self.game_state_timeout = time.time() + 1
                print("d[{i}] send data to vest: {hp}".format(i=self.pid, hp=vest_data))
        except Empty:
            try:
                if self.pid == 0 and not self.current_gun_state == 0:
                    if time.time() > self.game_state_timeout:
                        self.ch.write(self.current_gun_state)
                        self.game_state_timeout = time.time() + 1
                        #print("d[{i}] repeat data to gun: {bullets}".format(i=self.pid, bullets=self.current_gun_state))
                elif self.pid == 1 and not self.current_vest_state == 0:
                    if time.time() > self.game_state_timeout:
                        self.ch.write(self.current_vest_state)
                        self.game_state_timeout = time.time() + 1
                        #print("d[{i}] repeat data to vest: {hp}".format(i=self.pid, hp=self.current_vest_state))
            except btle.BTLEDisconnectError:
                if time.time() > self.game_state_timeout:
                    self.game_state_timeout = time.time() + 1
                self.connection = False

    def receive_data(self):
        try:
            self.peripheral.waitForNotifications(0.01)
        except btle.BTLEDisconnectError:
            print("Device[{id}] disconnected".format(id=self.pid))
            self.connection = False

    def communicate(self):
        if self.connection and self.handshake_done:
            self.send_data()
            self.receive_data()

    def run(self):
        self.setup_connection()
        while True:
            self.check_connection()
            self.do_handshake()
            self.communicate()


class CommunicationDelegate(btle.DefaultDelegate):
    def __init__(self, pid):
        self.pid = pid
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        d[self.pid].data += data

        buf_len = 20
        if self.pid == 2:
            buf_len = 40

        if len(d[self.pid].data) >= buf_len:
            indata = d[self.pid].data[0:20]

            if indata == ACK_H:
                d[self.pid].data = d[self.pid].data[20:]
            else:  # received data packet
                if not self.verify_valid_data():
                    indata = d[self.pid].data[0:20]
                    print("Device[{id}] received invalid data: {dat}".format(id=self.pid, dat=indata.hex()))
                else:
                    indata = d[self.pid].data[0:20]
                    d[self.pid].data = d[self.pid].data[20:]
                    c[0].data_to_cloud.put(indata)

    def verify_valid_data(self):
        # check & move to correct header
        header_index = 0
        if not ((d[self.pid].data[header_index] == 4 or d[self.pid].data[header_index] == 5 or d[self.pid].data[header_index] == 6) and (d[self.pid].data[header_index + 2] == 1 or d[self.pid].data[header_index + 2] == 2)):
            for i in range(len(d[self.pid].data)):
                if d[self.pid].data[i] == 6 and (d[self.pid].data[i + 2] == 1 or d[self.pid].data[i + 2] == 2):
                    header_index = i
                    d[self.pid].data = d[self.pid].data[header_index:]
                    break
            if len(d[self.pid].data) < 20:
                return False

        # verify checksum, return True if correct
        sum = 0
        for i in range(19):
            try:
                sum ^= int.from_bytes(d[self.pid].data[i], 'big')
            except TypeError:
                sum ^= d[self.pid].data[i]
        try:
            if sum == int.from_bytes(d[self.pid].data[19], 'big'):
                return True
        except TypeError:
            if sum == d[self.pid].data[19]:
                return True

        # (if checksum wrong) move to next header, return False
        for i in range(1, len(d[self.pid].data)):
            if d[self.pid].data[i] == 6 and (d[self.pid].data[i + 2] == 1 or d[self.pid].data[i + 2] == 2):
                header_index = i
                d[self.pid].data = d[self.pid].data[header_index:]
                break
        if len(d[self.pid].data) < 20:
            return False

        # check new checksum
        sum = 0
        for i in range(19):
            try:
                sum ^= int.from_bytes(d[self.pid].data[i], 'big')
            except TypeError:
                sum ^= d[self.pid].data[i]
        try:
            if sum == int.from_bytes(d[self.pid].data[19], 'big'):
                return True
        except TypeError:
            if sum == d[self.pid].data[19]:
                return True
        return False


class RelayNode(threading.Thread):
    def __init__(self, ip_addr, port_num):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (ip_addr, port_num)

        self.data_to_cloud = Queue()
        self.data_to_gun = Queue()
        self.data_to_vest = Queue()

        threading.Thread.__init__(self)

    def convert_to_json(self, data):
        try:
            packet = {
                "message_type": struct.unpack('>B', data[0:1])[0],
                "message_id": struct.unpack('>B', data[1:2])[0],
                "player_id": struct.unpack('>B', data[2:3])[0],
                "acc_x": struct.unpack('>h', data[7:9])[0],
                "acc_y": struct.unpack('>h', data[9:11])[0],
                "acc_z": struct.unpack('>h', data[11:13])[0],
                "gyro_x": struct.unpack('>h', data[13:15])[0],
                "gyro_y": struct.unpack('>h', data[15:17])[0],
                "gyro_z": struct.unpack('>h', data[17:19])[0],
                "timestamp": struct.unpack('>L', data[3:7])[0]
            }
            return json.dumps(packet)
        except struct.error:
            print(data)

    def extract_msg(self, msg):
        # default value
        bullets = 6
        hp = 10
        shield = 0

        if PLAYER_ID == b'\x01':
            bullets = msg["p1"]["bullets"]
            hp = int(msg["p1"]["hp"] / 10)
            shield = int(msg["p1"]["shield_health"] / 10)
        elif PLAYER_ID == b'\x02':
            bullets = msg["p2"]["bullets"]
            hp = int(msg["p2"]["hp"] / 10)
            shield = int(msg["p2"]["shield_health"] / 10)

        print(msg)
        print("bullet={b}, hp={v}, shield_health={s}".format(b=bullets, v=hp, s=shield))

        bullets = (bullets << 4) | 128
        hp = ((shield << 5) + (hp << 1)) | 128

        self.data_to_gun.put(bullets)
        self.data_to_vest.put(hp)

    def connect_server(self):
        self.socket.connect(self.server_address)
        self.socket.setblocking(0)

    def send_data(self):
        try:
            msg = self.convert_to_json(self.data_to_cloud.get_nowait())
            msg_length = str(len(msg)) + '_'
            try:
                self.socket.sendall(msg_length.encode("utf-8"))
                self.socket.sendall(msg.encode("utf-8"))
            except OSError:
                print("connection between relay_client and relay_server lost")
        except Empty:
            return

    def receive_data(self):
        try:
            self.socket.setblocking(0)
            data = b''
            while True:
                _d = self.socket.recv(1)
                if not _d:
                    data = b''
                    break
                try:
                    data += _d
                    int(data)
                except ValueError:
                    data = data[:-1]
                    break
            if len(data) == 0:
                print('no more data from relay_server')
                return

            data = data.decode("utf-8")
            length = int(data)

            self.socket.setblocking(1)
            data = b''
            while len(data) < length:
                _d = self.socket.recv(length - len(data))
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                return
            msg = json.loads(data.decode("utf8"))  # Decode raw bytes to UTF-8
            self.extract_msg(msg)
            self.socket.setblocking(0)

        except BlockingIOError:
            return

        except ConnectionResetError:
            return

    def run(self):
        self.connect_server()
        while True:
            self.send_data()
            self.receive_data()


if __name__ == "__main__":
    address = '127.0.0.1'
    port = 8049

    threads = list()

    for x in range(nBeetle):
        d.append(PeripheralDevice(x))
        threads.append(d[x])

    c.append(RelayNode(address, port))
    threads.append(c[0])

    for t in threads:
        t.start()

    for t in threads:
        t.join()
