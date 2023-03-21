from bluepy import btle
from pathlib import Path
from datetime import date
import os
import sys

import threading
import time

# for debugging purpose
need_elapsed_time = True
need_n_packet_received = False
need_n_packet_fragmented = False
need_n_packet_loss = False
need_n_corrupt = False
need_better_display = False
need_write_to_file = True

ACTION_NUM = sys.argv[1]
DATA_LENGTH = 40
# 1 - grenade
# 2 - reload
# 3 - shield
# 4 - log out

file_path = "data_" + str(date.today())
file_index = 1
file_name = "imu_data_" + str(date.today())
is_movement_detected = False
file_length = 0

if need_better_display:
    import curses

if need_write_to_file:
    import struct

ACK = b'\x41'
NAK = b'\x4E'

REQUEST_H = b'\x48'
ACK_H = b'\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x40'

nBeetle = 1

mac = list()

# mac.append('80:30:dc:e9:1c:74') # imu X
mac.append('80:30:dc:e9:08:d7')  # imu

d = list()  # devices list


class PeripheralInfo():  # use for storing info and flags of each peripheral
    def __init__(self):
        self.peripheral = 0  # btle.Peripheral()
        self.svc = 0
        self.ch = 0
        self.setup = 0
        self.connection = 0
        self.handshake_start = 0
        self.handshake_done = 0
        self.data = 0  # bytearray(b'')

        if need_n_corrupt:
            self.error_count = 0

        if need_elapsed_time:
            self.start_time = 0

        if need_n_packet_received:
            self.n_packet_received = 0

        if need_n_packet_fragmented:
            self.n_time_received = -1  # don't count first packet (handshake ack)
            self.n_time_sent = 0
            self.n_fragment = 0

        if need_n_packet_loss:
            self.n_packet_loss = 0
            self.prev_msg_id = -1


class CommunicationDelegate(btle.DefaultDelegate):
    def __init__(self, pid):
        self.pid = pid
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        d[self.pid].data += data
        # d[self.pid].data = data

        if need_n_packet_fragmented:
            d[self.pid].n_time_received += 1

        # if len(d[self.pid].data) >= 20:
        if len(d[self.pid].data) >= 40:
            indata = d[self.pid].data[0:20]
            # d[self.pid].data = d[self.pid].data[20:]

            d[self.pid].handshake_done = 1
            if indata == ACK_H:
                if need_better_display:
                    stdscr.addstr((self.pid * info_row), 0, "Device[{id}] handshake ACK received".format(id=self.pid))
                    stdscr.refresh()
                else:
                    print("Device[{id}] handshake ACK received".format(id=self.pid))
                # d[self.pid].ch.write(ACK)
                # if not self.pid == 2:  # no ack for imu
                #    d[self.pid].ch.write(ACK)

                if need_elapsed_time:
                    if d[self.pid].start_time == 0:
                        d[self.pid].start_time = time.time()

                d[self.pid].data = d[self.pid].data[20:]  ###
            else:
                # reorderData(indata)
                # if not verifyValidData(indata):
                if not verifyValidData(self.pid):
                    # indata = d[self.pid].data[0:20]
                    if not need_better_display:
                        print("Device[{id}] received invalid data".format(id=self.pid))
                        print("Device[{id}] received: {dat}".format(id=self.pid, dat=indata.hex()))
                        indata = d[self.pid].data[0:20]
                        print("Device[{id}] received: {dat}".format(id=self.pid, dat=indata.hex()))
                        print("Elapsed time: {time}".format(time=time.time() - d[self.pid].start_time))
                    if need_n_corrupt:
                        d[self.pid].error_count += 1
                    if need_n_packet_fragmented:
                        d[self.pid].n_fragment += 1
                else:
                    indata = d[self.pid].data[0:20]
                    if need_write_to_file:
                        writeToFile(indata)

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

                    d[self.pid].data = d[self.pid].data[20:]  ###

                if need_n_packet_received:
                    d[self.pid].n_packet_received += 1

                if need_n_packet_fragmented:
                    d[self.pid].n_time_sent += 1

                if need_better_display:
                    stdscr.addstr((self.pid * info_row), 0,
                                  "Device[{id}] received: {dat}".format(id=self.pid, dat=indata.hex()))
                    stdscr.refresh()
                # else:
                # print("Device[{id}] received: {dat}".format(id=self.pid, dat=indata.hex()))

                if need_n_packet_received:
                    if need_better_display:
                        stdscr.addstr((self.pid * info_row + 1), 0,
                                      "Device[{id}] have received {n} packets".format(id=self.pid,
                                                                                      n=d[self.pid].n_packet_received))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] have received {n} packets".format(id=self.pid,
                                                                              n=d[self.pid].n_packet_received))

                if need_n_corrupt:
                    if need_better_display:
                        stdscr.addstr((self.pid * info_row + 2), 0,
                                      "Device[{id}] have received {n} corrupted packets".format(id=self.pid, n=d[
                                          self.pid].error_count))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] have received {n} corrupted packets".format(id=self.pid,
                                                                                        n=d[self.pid].error_count))

                if need_n_packet_fragmented:
                    if need_better_display:
                        stdscr.addstr((self.pid * info_row + 2), 0,
                                      "Device[{id}] have detected {n} fragmented packets".format(id=self.pid, n=d[
                                          self.pid].n_fragment))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] have detected {n} fragmented packets".format(id=self.pid,
                                                                                         n=d[self.pid].n_time_received -
                                                                                           d[self.pid].n_time_sent + d[
                                                                                               self.pid].n_fragment))

                if need_n_packet_loss:
                    if need_better_display:
                        stdscr.addstr((self.pid * info_row + 4), 0,
                                      "Device[{id}] have {n} packets loss".format(id=self.pid,
                                                                                  n=d[self.pid].n_packet_loss))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] have {n} packets loss".format(id=self.pid, n=d[self.pid].n_packet_loss))

                if need_elapsed_time:
                    if need_better_display:

                        stdscr.addstr((self.pid * info_row + 3), 0,
                                      "Elapsed time: {time}".format(time=time.time() - d[self.pid].start_time))
                        stdscr.refresh()


class ImuData:
    def __init__(self, msg_id):
        self.id = msg_id
        self.acc_x = -1
        self.acc_y = -1
        self.acc_z = -1
        self.gyro_x = -1
        self.gyro_y = -1
        self.gyro_z = -1
        self.timestamp = -1

    def is_moving(self):
        if self.acc_x + self.acc_y + self.acc_z + self.gyro_x + self.gyro_y + self.gyro_z == 0:
            return True
        return True


def get_file_index():
    if(not os.path.exists(file_path)):
        os.mkdir(file_path)
    global file_name, file_index
    data_file_path = f"""./{file_path}/{file_name}_Action_{ACTION_NUM}_{file_index}.csv"""
    path = Path(data_file_path)
    while (path.is_file()):
        file_index += 1
        data_file_path = f"""./{file_path}/{file_name}_Action_{ACTION_NUM}_{file_index}.csv"""
        path = Path(data_file_path)


def writeToFile(indata):
    global file_index, is_movement_detected, file_name, file_length

    imu_indata = ImuData(indata[1])

    imu_indata.timestamp = struct.unpack('>L', indata[3:7])[0]
    imu_indata.acc_x = struct.unpack('>h', indata[7:9])[0]
    imu_indata.acc_y = struct.unpack('>h', indata[9:11])[0]
    imu_indata.acc_z = struct.unpack('>h', indata[11:13])[0]
    imu_indata.gyro_x = struct.unpack('>h', indata[13:15])[0]
    imu_indata.gyro_y = struct.unpack('>h', indata[15:17])[0]
    imu_indata.gyro_z = struct.unpack('>h', indata[17:19])[0]

    with open("AA_rawdata.csv", "a") as f:
        f.write(
            f"""{imu_indata.timestamp},{ACTION_NUM},{imu_indata.acc_x},{imu_indata.acc_y},{imu_indata.acc_z},{imu_indata.gyro_x},{imu_indata.gyro_y},{imu_indata.gyro_z}\n""")
        f.close()
    # print( f"""{imu_indata.timestamp},{ACTION_NUM},{imu_indata.acc_x},{imu_indata.acc_y},{imu_indata.acc_z},{imu_indata.gyro_x},{imu_indata.gyro_y},{imu_indata.gyro_z}\n""")

    imu_filename = f"""./{file_path}/{file_name}_Action_{ACTION_NUM}_{file_index}.csv"""
    if imu_indata.is_moving():
        is_movement_detected = True
        file_length = file_length + 1
        with open(imu_filename, "a") as f:
            f.write(
                f"""{imu_indata.timestamp},{ACTION_NUM},{imu_indata.acc_x},{imu_indata.acc_y},{imu_indata.acc_z},{imu_indata.gyro_x},{imu_indata.gyro_y},{imu_indata.gyro_z}\n""")
            f.close()

    else:
        if is_movement_detected:
            if file_length >= DATA_LENGTH:
                print(f"""{imu_filename} saved""")
                file_index = file_index + 1
            else:
                print(file_length)
                file_length = 0

                with open(imu_filename, "w") as f:
                    f.write("")
                    f.close()
                os.remove(imu_filename)
            file_length = 0
        is_movement_detected = False


def verifyValidData(id):
    # check & move to correct header
    header_index = 0
    if not ((d[id].data[header_index] == 4 or d[id].data[header_index] == 5 or d[id].data[header_index] == 6) and (
            d[id].data[header_index + 2] == 1 or d[id].data[header_index + 2] == 2)):
        # print("Header not correct: {header}".format(header=d[id].data[header_index]))
        for x in range(len(d[id].data)):
            if d[id].data[x] == 6 and (d[id].data[x + 2] == 1 or d[id].data[x + 2] == 2):
                header_index = x
                d[id].data = d[id].data[header_index:]
                break
        if len(d[id].data) < 20:
            return False

    # verify checksum, return True if correct
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

    for x in range(1, len(d[id].data)):
        if d[id].data[x] == 6 and (d[id].data[x + 2] == 1 or d[id].data[x + 2] == 2):
            header_index = x
            d[id].data = d[id].data[header_index:]
            break
    if len(d[id].data) < 20:
        return False

    # check new checksum
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
        stdscr.addstr((i * info_row), 0, "Connecting device {id}".format(id=i))
        stdscr.refresh()
    timeout = 0
    try:
        d[i].peripheral.connect(mac[i])
        d[i].connection = 1
        d[i].peripheral.setDelegate(CommunicationDelegate(i))
        d[i].svc = d[i].peripheral.getServiceByUUID('0000dfb0-0000-1000-8000-00805f9b34fb')
        d[i].ch = d[i].svc.getCharacteristics()[0]
        d[i].setup = 1
        if need_better_display:
            stdscr.addstr((i * info_row), 0, "Device[{id}] connected".format(id=i))
            stdscr.refresh()
        else:
            print("Device[{id}] connected".format(id=i))
    except btle.BTLEDisconnectError:
        if need_better_display:
            stdscr.addstr((i * info_row), 0, "Device[{id}] not connected".format(id=i))
            stdscr.refresh()
        else:
            print("Device[{id}] not connected".format(id=i))
    except AttributeError:
        if need_better_display:
            stdscr.addstr((i * info_row), 0, "Device[{id}] not connected".format(id=i))
            stdscr.refresh()
        else:
            print("Device[{id}] not connected".format(id=i))
        time.sleep(1)

    while True:
        try:
            if d[i].setup == 0:  # check setup
                if need_better_display:
                    stdscr.addstr((i * info_row), 0, "Try setting up device[{id}] again".format(id=i))
                    stdscr.refresh()
                else:
                    print("Try setting up device[{id}] again".format(id=i))
                try:
                    d[i].peripheral.connect(mac[i])
                    d[i].connection = 1
                    d[i].peripheral.setDelegate(CommunicationDelegate(i))
                    d[i].svc = d[i].peripheral.getServiceByUUID('0000dfb0-0000-1000-8000-00805f9b34fb')
                    d[i].ch = d[i].svc.getCharacteristics()[0]
                    d[i].setup = 1
                    if need_better_display:
                        stdscr.addstr((i * info_row), 0, "Device[{id}] connected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] connected".format(id=i))
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr((i * info_row), 0, "Device[{id}] still not connected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] still not connected".format(id=i))
                except AttributeError:
                    if need_better_display:
                        stdscr.addstr((i * info_row), 0, "Device[{id}] not connected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] not connected".format(id=i))
                    time.sleep(1)
            elif d[i].connection == 0:  # check connection
                if need_better_display:
                    stdscr.addstr((i * info_row), 0,
                                  "Reconnecting device[{id}]                                      ".format(id=i))
                    stdscr.refresh()
                else:
                    print("Reconnecting device[{id}]".format(id=i))
                try:
                    d[i].peripheral.connect(mac[i])
                    d[i].connection = 1
                    d[i].handshake_start = 0
                    d[i].handshake_done = 0
                    if need_better_display:
                        stdscr.addstr((i * info_row), 0, "Device[{id}] connected   ".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] connected".format(id=i))
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr((i * info_row), 0, "Device[{id}] not connected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] not connected".format(id=i))
            elif d[i].handshake_start == 0:  # check handshake has begun
                try:
                    time.sleep(5)
                    timeout = time.time() + 10  # 10s from now
                    d[i].ch.write(REQUEST_H)
                    d[i].handshake_start = 1
                    if need_better_display:
                        stdscr.addstr((i * info_row), 0, "Device[{id}] begin handshake".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] begin handshake".format(id=i))
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr((i * info_row), 0, "Device[{id}] disconnected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] disconnected".format(id=i))
                    d[i].connection = 0
            elif d[i].handshake_done == 0:  # check handshake is done
                if need_better_display:
                    stdscr.addstr((i * info_row), 0, "Device[{id}] waiting handshake ACK...".format(id=i))
                    stdscr.refresh()
                else:
                    print("Device[{id}] waiting handshake ACK...".format(id=i))
                try:
                    d[i].peripheral.waitForNotifications(1.0)
                    if time.time() > timeout:
                        if need_better_display:
                            stdscr.addstr((i * info_row), 0, "Device[{id}] resend handshake".format(id=i))
                            stdscr.refresh()
                        else:
                            print("Device[{id}] resend handshake".format(id=i))
                        d[i].handshake_start = 0
                        d[i].handshake_done = 0
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr((i * info_row), 0, "Device[{id}] disconnected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] disconnected".format(id=i))
                    d[i].connection = 0
            else:  # normal communication

                try:
                    d[i].peripheral.waitForNotifications(1.0)
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr((i * info_row), 0, "Device[{id}] disconnected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] disconnected".format(id=i))
                    d[i].connection = 0


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


if __name__ == "__main__":
    threads = list()
    get_file_index()

    if need_better_display:
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

        stdscr = curses.initscr()
        stdscr.clear()
        stdscr.refresh()

    for i in range(nBeetle):
        t = threading.Thread(target=handleBeetle, args=(i,))
        threads.append(t)

    for t in threads:
        t.start()
