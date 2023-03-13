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

import struct
import curses

#for debugging purpose
need_elapsed_time = True
need_n_packet_received = True
need_n_packet_fragmented = False
need_n_packet_loss = False
need_n_corrupt = False
need_better_display = False
need_write_to_file = False

PLAYER_ID = b'\x02' # \x01 or \x02

ACK = b'\x41'
NAK = b'\x4E'

REQUEST_H = b'\x48'
ACK_H = b'\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x40'

nBeetle = 3

mac = list()
if PLAYER_ID == b'\x01':
    mac.append('80:30:dc:d9:1f:93')  # gun x
    mac.append('34:15:13:22:a1:37')  # vest x
    mac.append('80:30:dc:e9:1c:74')  # imu X
elif PLAYER_ID == b'\x02':
    mac.append('34:14:b5:51:d9:04') # gun
    mac.append('80:30:dc:d9:23:27') # vest
    mac.append('80:30:dc:e9:08:d7') # imu

d = list() #devices list
c = list() #connection to cloud

class PeripheralInfo(): #use for storing info and flags of each peripheral
    def __init__(self):
        self.peripheral = 0
        self.svc = 0
        self.ch = 0
        self.setup = 0
        self.connection = 0
        self.handshake_start = 0
        self.handshake_done = 0
        self.data = 0 #bytearray(b'')

        if need_n_corrupt:
            self.error_count = 0

        if need_elapsed_time:
            self.start_time = 0

        if need_n_packet_received:
            self.n_packet_received = 0

        if need_n_packet_fragmented:
            self.n_time_received = -1 #don't count first packet (handshake ack)
            self.n_time_sent = 0
            self.n_fragment = 0

        if need_n_packet_loss:
            self.n_packet_loss = 0
            self.prev_msg_id = -1


class RelayNode():
    def __init__(self, ip_addr, port_num):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (ip_addr, port_num)

        #self.data_to_cloud = 0
        #self.data_to_hw = 0
        self.data_to_cloud = Queue()
        self.data_to_gun = Queue()
        self.data_to_vest = Queue()

class CommunicationDelegate(btle.DefaultDelegate):
    def __init__(self, pid):
        self.pid = pid
        btle.DefaultDelegate.__init__(self)
    def handleNotification(self, cHandle, data):
        d[self.pid].data += data

        if need_n_packet_fragmented:
            d[self.pid].n_time_received += 1

        buf_len = 20
        if self.pid == 2:
            buf_len = 40
        if len(d[self.pid].data) >= buf_len:
            indata = d[self.pid].data[0:20]

            d[self.pid].handshake_done = 1
            if indata == ACK_H:
                displayOutput(self.pid * info_row, "Device[{id}] handshake ACK received".format(id=self.pid))
                #if not self.pid == 2:  # no ack for imu
                    #d[self.pid].ch.write(ACK)

                if need_elapsed_time:
                    if d[self.pid].start_time == 0:
                        d[self.pid].start_time = time.time()

                d[self.pid].data = d[self.pid].data[20:]
            else:
                if not verifyValidData(self.pid):
                    indata = d[self.pid].data[0:20]
                    if not need_better_display:
                        print("Device[{id}] received invalid data: {dat}".format(id=self.pid, dat=indata.hex()))
                    if need_n_corrupt:
                        d[self.pid].error_count += 1
                    if need_n_packet_fragmented:
                        d[self.pid].n_fragment += 1
                else:
                    indata = d[self.pid].data[0:20]
                    if need_write_to_file:
                        writeToFile("./imu_data", indata)
                    if need_n_packet_loss:
                        if d[self.pid].prev_msg_id == -1:
                            d[self.pid].prev_msg_id = indata[1]
                        else:
                            if indata[0] == 4 or indata[0] == 5:
                                if indata[1] == d[self.pid].prev_msg_id:
                                    d[self.pid].n_packet_loss += 1
                            elif indata[0] == 6:
                                if indata[1] < d[self.pid].prev_msg_id:
                                    d[self.pid].n_packet_loss += (indata[1] + 10) - d[self.pid].prev_msg_id - 1
                                else:
                                    d[self.pid].n_packet_loss += abs(indata[1] - d[self.pid].prev_msg_id - 1)
                            d[self.pid].prev_msg_id = indata[1]
                    d[self.pid].data = d[self.pid].data[20:]

                    c[0].data_to_cloud.put(indata)
                    if indata[0] != 6:
                        print("put data to cloud in queue: {ts}".format(ts=time.time()))

                if need_n_packet_received:
                    d[self.pid].n_packet_received += 1

                if need_n_packet_fragmented:
                    d[self.pid].n_time_sent += 1

                #c[0].data_to_cloud += indata
                #c[0].data_to_cloud.put(indata) #only put to cloud when valid data
                #displayOutput(self.pid * info_row, "Device[{id}] received: {dat}".format(id=self.pid, dat=indata.hex()))


                ###if need_n_packet_received:
                    ###displayOutput(self.pid * info_row + 1, "Device[{id}] have received {n} packets".format(id=self.pid, n=d[self.pid].n_packet_received))

                if need_n_corrupt:
                    displayOutput(self.pid * info_row + 2, "Device[{id}] have received {n} corrupted packets".format(id=self.pid, n=d[self.pid].error_count))

                if need_n_packet_fragmented:
                    displayOutput(self.pid * info_row + 2, "Device[{id}] have detected {n} fragmented packets".format(id=self.pid, n=d[self.pid].n_time_received-d[self.pid].n_time_sent+d[self.pid].n_fragment))

                if need_n_packet_loss:
                    displayOutput(self.pid*info_row+4, "Device[{id}] have {n} packets loss".format(id=self.pid, n=d[self.pid].n_packet_loss))

                ###if need_elapsed_time:
                    ###displayOutput(self.pid*info_row+3, "Elapsed time: {time}".format(time=time.time()-d[self.pid].start_time))

                #if not self.pid == 2: #no ack for imu
                    #d[self.pid].ch.write(ACK)

if need_write_to_file:
    def writeToFile(filename, indata):
        imudata = list()
        if indata[0] == 6:
            imudata.append("{id} acc_x: {data}\n".format(id=indata[1], data=struct.unpack('>f',indata[3:7])))
            imudata.append("{id} acc_y: {data}\n".format(id=indata[1], data=struct.unpack('>f',indata[7:11])))
            imudata.append("{id} acc_z: {data}\n".format(id=indata[1], data=struct.unpack('>f', indata[11:15])))
        elif indata[0] == 22:
            imudata.append("{id} gyro_x: {data}\n".format(id=indata[1], data=struct.unpack('>f', indata[3:7])))
            imudata.append("{id} gyro_y: {data}\n".format(id=indata[1], data=struct.unpack('>f', indata[7:11])))
            imudata.append("{id} gyro_z: {data}\n".format(id=indata[1], data=struct.unpack('>f', indata[11:15])))

        with open(filename, "a") as f:
            for i in range(3):
                f.write(imudata[i])


def displayOutput(row, output):
    if need_better_display:
        stdscr.addstr(row, 0, output)
        stdscr.refresh()
    else:
        print(output)


def verifyValidData(id):
    #check & move to correct header
    header_index = 0
    if not ((d[id].data[header_index] == 4 or d[id].data[header_index] == 5 or d[id].data[header_index] == 6) and (d[id].data[header_index+2] == 1 or d[id].data[header_index+2] == 2)):
        for x in range(len(d[id].data)):
            if d[id].data[x] == 6 and (d[id].data[x+2] == 1 or d[id].data[x+2] == 2):
                header_index = x
                d[id].data = d[id].data[header_index:]
                break
        if len(d[id].data) < 20:
            return False

    #verify checksum, return True if correct
    sum = 0
    for x in range(19):
        try:
            sum ^= int.from_bytes(d[id].data[x], 'big')
        except TypeError:
            sum ^= d[id].data[x]
    try:
        if sum == int.from_bytes(d[id].data[19], 'big'):
            return True
    except TypeError:
        if sum == d[id].data[19]:
            return True

    #(if checksum wrong) move to next header, return False
    for x in range(1, len(d[id].data)):
        if d[id].data[x] == 6 and (d[id].data[x + 2] == 1 or d[id].data[x + 2] == 2):
            header_index = x
            d[id].data = d[id].data[header_index:]
            break
    if len(d[id].data) < 20:
        return False

    #check new checksum
    sum = 0
    for x in range(19):
        try:
            sum ^= int.from_bytes(d[id].data[x], 'big')
        except TypeError:
            sum ^= d[id].data[x]
    try:
        if sum == int.from_bytes(d[id].data[19], 'big'):
            return True
    except TypeError:
        if sum == d[id].data[19]:
            return True
    return False


def handleBeetle(i):
    d.append(PeripheralInfo())
    d[i].peripheral = btle.Peripheral()
    d[i].data = bytearray(b'')
    if need_better_display:
        displayOutput(i*info_row, "Connecting device {id}".format(id=i))
    timeout = 0
    try:
        d[i].peripheral.connect(mac[i])
        d[i].connection = 1
        d[i].peripheral.setDelegate(CommunicationDelegate(i))
        d[i].svc = d[i].peripheral.getServiceByUUID('0000dfb0-0000-1000-8000-00805f9b34fb')
        d[i].ch = d[i].svc.getCharacteristics()[0]
        d[i].setup = 1
        displayOutput(i*info_row, "Device[{id}] connected".format(id=i))
    except btle.BTLEDisconnectError:
        displayOutput(i*info_row, "Device[{id}] not connected".format(id=i))
    except AttributeError:
        displayOutput(i*info_row, "Device[{id}] not connected".format(id=i))
        time.sleep(1)

    while True:
        try:
            if d[i].setup == 0: #check setup
                displayOutput(i*info_row, "Try setting up device[{id}] again".format(id=i))
                try:
                    d[i].peripheral.connect(mac[i])
                    d[i].connection = 1
                    d[i].peripheral.setDelegate(CommunicationDelegate(i))
                    d[i].svc = d[i].peripheral.getServiceByUUID('0000dfb0-0000-1000-8000-00805f9b34fb')
                    d[i].ch = d[i].svc.getCharacteristics()[0]
                    d[i].setup = 1
                    displayOutput(i*info_row, "Device[{id}] connected".format(id=i))
                except btle.BTLEDisconnectError:
                    displayOutput(i * info_row, "Device[{id}] still not connected".format(id=i))
                except AttributeError:
                    displayOutput(i * info_row, "Device[{id}] not connected".format(id=i))
                    time.sleep(1)
            elif d[i].connection == 0: #check connection
                displayOutput(i * info_row, "Reconnecting device[{id}]                                      ".format(id=i))
                try:
                    d[i].peripheral.connect(mac[i])
                    d[i].connection = 1
                    d[i].handshake_start = 0
                    d[i].handshake_done = 0
                    displayOutput(i * info_row, "Device[{id}] connected   ".format(id=i))
                except btle.BTLEDisconnectError:
                    displayOutput(i * info_row, "Device[{id}] not connected".format(id=i))
            elif d[i].handshake_start == 0:  # check handshake has begun
                try:
                    time.sleep(5)
                    timeout = time.time() + 10  # 10s from now
                    d[i].ch.write(REQUEST_H)
                    d[i].handshake_start = 1
                    displayOutput(i * info_row, "Device[{id}] begin handshake".format(id=i))
                except btle.BTLEDisconnectError:
                    displayOutput(i * info_row, "Device[{id}] disconnected".format(id=i))
                    d[i].connection = 0
            elif d[i].handshake_done == 0:  # check handshake is done
                displayOutput(i * info_row, "Device[{id}] waiting handshake ACK...".format(id=i))
                try:
                    d[i].peripheral.waitForNotifications(1.0)
                    if time.time() > timeout:
                        '''
                        if need_better_display:
                            stdscr.addstr((i*info_row), 0, "Device[{id}] resend handshake".format(id=i))
                            stdscr.refresh()
                        else:
                            print("Device[{id}] resend handshake".format(id=i))
                        '''
                        displayOutput(i * info_row, "Device[{id}] resend handshake".format(id=i))
                        d[i].handshake_start = 0
                        d[i].handshake_done = 0
                except btle.BTLEDisconnectError:
                    displayOutput(i * info_row, "Device[{id}] disconnected".format(id=i))
                    d[i].connection = 0
            else:  # normal communication
                # if got data to send to hw
                #print("NORMAL COMM on {n}".format(n=i))
                try:
                    if i == 0:
                        #print("d[{i}] prepare data to gun".format(i=i))
                        gun_data = c[0].data_to_gun.get_nowait()
                        if not need_better_display:
                            print("d[{i}] send data to gun: {bullets}".format(i=i, bullets=gun_data))
                        gun_data_b = gun_data.to_bytes(1, 'big')
                        d[i].ch.write(gun_data_b)
                    elif i == 1:
                        #print("d[{i}] prepare data to vest".format(i=i))
                        vest_data = c[0].data_to_vest.get_nowait()
                        if not need_better_display:
                            print("d[{i}] send data to vest: {hp}".format(i=i, hp=vest_data))
                        vest_data_b = vest_data.to_bytes(1, 'big')
                        d[i].ch.write(vest_data_b)
                except Empty:
                    #print("EMPTY DATA TO HW")
                    pass

                ###if not need_better_display:
                 ###   displayOutput(i * info_row, "Device[{id}] waiting...".format(id=i))
                try:
                    d[i].peripheral.waitForNotifications(0.01)
                except btle.BTLEDisconnectError:
                    displayOutput(i * info_row, "Device[{id}] disconnected".format(id=i))
                    d[i].connection = 0

                # testing only, send for 10s
                #if (time.time() - d[i].start_time >= 10) and (time.time() - d[i].start_time <= 1000):
                #    return

                #for testing only, send 1000 bytes
                #if d[i].n_packet_received >= 1000:
                #    return

        except btle.BTLEInternalError:
            d[i].peripheral = btle.Peripheral()
            d[i].svc = 0
            d[i].ch = 0
            d[i].setup = 0
            d[i].connection = 0
            d[i].handshake_start = 0
            d[i].handshake_done = 0
            d[i].data = bytearray(b'')
            if need_elapsed_time:
                d[i].start_time = 0

            if need_n_packet_received:
                d[i].n_packet_received = 0

            if need_n_packet_fragmented:
                d[i].n_time_received = -1
                d[i].n_time_sent = 0

            if need_n_packet_loss:
                d[i].n_packet_loss = 0
                d[i].prev_msg_id = 0


def convert_to_json(data):
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

        if packet["message_type"] != 6:
            print(packet)
        return json.dumps(packet)

    except struct.error:
        print(data)


def extractMsg(msg):
    #default value
    bullets = 6
    hp = 10
    shield = 0 #for testing only

    if PLAYER_ID == b'\x01':
        bullets = msg["p1"]["bullets"]
        hp = int(msg["p1"]["hp"] / 10)
        shield = int(msg["p1"]["shield_health"] / 10)
    elif PLAYER_ID == b'\x02':
        bullets = msg["p2"]["bullets"]
        hp = int(msg["p2"]["hp"] /10)
        shield = int(msg["p2"]["shield_health"] / 10)

    print("bullet={b}, hp={v}, shield_health={s}".format(b=bullets, v=hp, s=shield))

    bullets = (bullets << 4) | 128
    hp = ((shield << 5) + (hp << 1)) | 128

    #d[0].ch.write(bullets.to_bytes(1, 'big'))
    #d[1].ch.write(hp.to_bytes(1, 'big'))

    print("bullet = {b}".format(b=hex(bullets)))
    print("shield+hp = {sh}".format(sh=hex(hp)))
    c[0].data_to_gun.put(bullets)
    c[0].data_to_vest.put(hp)


def getCs(inByte):
    cs = 0
    for i in range(8):
        cs ^= (inByte << i)

    cs &= 1
    return inByte | cs



def handleConnection():
    ip_addr = '127.0.0.1'
    port_num = 8049
    c.append(RelayNode(ip_addr, port_num))
    c[0].data_to_cloud = Queue()
    c[0].data_to_hw = Queue()
    c[0].data_to_gun = Queue()
    c[0].data_to_vest = Queue()

    c[0].socket.connect(c[0].server_address)

    c[0].socket.setblocking(0)

    while True:
        #print("HANDLE CONNECTION")
        #send data
        try:
            msg_b = c[0].data_to_cloud.get_nowait()
            msg = convert_to_json(msg_b)
            #msg = convert_to_json(c[0].data_to_cloud.get_nowait())
            if msg_b[0] != 6:
                print("get data to cloud from queue: {ts}".format(ts=time.time()))
            #print(msg)
            msg_length = str(len(msg)) + '_'

            try:
                c[0].socket.sendall(msg_length.encode("utf-8"))
                c[0].socket.sendall(msg.encode("utf-8"))
                if (not need_better_display) and msg_b[0] != 6:
                    print(msg)
                    print("data sent to cloud: {ts}".format(ts=time.time()))
            except OSError:
                if not need_better_display:
                    print("connection between relay_client and relay_server lost")

        except Empty:
            #print("empty!!!!!!!!!!!!!!!")
            pass
            #continue
            #if not need_better_display:
                #print("Empty Queue")

        #receive data
        try:
            c[0].socket.setblocking(0)
            data = b''
            while True:
                _d = c[0].socket.recv(1)
                if not _d:
                    data = b''
                    break
                try:
                    data += _d
                    int(data)
                except ValueError:
                    data = data[:-1]
                    break
            '''
            while not data.endswith(b'_'):
                _d = c[0].socket.recv(1)
                if not _d:
                    data = b''
                    break
                data += _d
            '''
            if len(data) == 0:
                print('no more data from relay_server')
                #c[0].stop()
                continue

            data = data.decode("utf-8")
            length = int(data)

            c[0].socket.setblocking(1)
            data = b''
            while len(data) < length:
                _d = c[0].socket.recv(length - len(data))
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                #print('no more data from relay_server')
                #c[0].stop()
                continue
            msg = json.loads(data.decode("utf8"))  # Decode raw bytes to UTF-8
            #print(msg)
            extractMsg(msg)

        except BlockingIOError:
            continue

        except ConnectionResetError:
            print('Connection Reset')
            continue
            #self.stop()


if __name__ == "__main__":
    threads = list()

    info_row = 6
    '''
    info_row = 1
    if need_elapsed_time:
        info_row += 1
    if need_n_packet_received:
        info_row += 1
    if need_n_packet_fragmented:
        info_row += 1
    if need_n_packet_loss:
        info_row += 1
    if need_n_corrupt:
        info_row += 1
    '''

    if need_better_display:
        stdscr = curses.initscr()
        stdscr.clear()
        stdscr.refresh()

    for x in range(nBeetle):
        t = threading.Thread(target=handleBeetle, args=(x,))
        threads.append(t)

    t = threading.Thread(target=handleConnection)
    threads.append(t)

    for t in threads:
        t.start()
        #t.join() #
