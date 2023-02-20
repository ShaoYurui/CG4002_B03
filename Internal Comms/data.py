from bluepy import btle

import threading
import time

#for debugging purpose
need_elapsed_time = True
need_n_packet_received = False
need_n_packet_fragmented = False
need_n_packet_loss = False
need_n_corrupt = False
need_better_display = False
need_write_to_file = True
ACTION_NUM = 1


file_index = 1
file_name = "imu_data"
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
#mac.append('80:30:dc:d9:1f:93') # gun
#mac.append('80:30:dc:d9:23:27') # vest
#mac.append('34:15:13:22:a1:37') # vest
#mac.append('80:30:dc:e9:1c:74') # imu X
mac.append('80:30:dc:e9:08:d7') # imu
##mac.append('34:14:b5:51:d9:04') # temp imu

d = list() #devices list

class PeripheralInfo(): #use for storing info and flags of each peripheral
    def __init__(self):
        self.peripheral = 0 #btle.Peripheral()
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


class CommunicationDelegate(btle.DefaultDelegate):
    def __init__(self, pid):
        self.pid = pid
        btle.DefaultDelegate.__init__(self)
    def handleNotification(self, cHandle, data):
        d[self.pid].data += data

        if need_n_packet_fragmented:
            d[self.pid].n_time_received += 1

        if len(d[self.pid].data) >= 20:
            indata = d[self.pid].data[0:20]
            d[self.pid].data = d[self.pid].data[20:]

            d[self.pid].handshake_done = 1
            if indata == ACK_H:
                if need_better_display:
                    stdscr.addstr((self.pid * info_row), 0, "Device[{id}] handshake ACK received".format(id=self.pid))
                    stdscr.refresh()
                else:
                    print("Device[{id}] handshake ACK received".format(id=self.pid))
                # d[self.pid].ch.write(ACK)
                #if not self.pid == 2:  # no ack for imu
                #    d[self.pid].ch.write(ACK)

                if need_elapsed_time:
                    if d[self.pid].start_time == 0:
                        d[self.pid].start_time = time.time()
            else:
                reorderData(indata)
                if not verifyValidData(indata):
                    if not need_better_display:
                        print("Device[{id}] received invalid data".format(id=self.pid))
                        print("Device[{id}] received: {dat}".format(id=self.pid, dat=indata.hex()))
                    if need_n_corrupt:
                        d[self.pid].error_count += 1
                    if need_n_packet_fragmented:
                        d[self.pid].n_fragment += 1
                else:
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

                if need_n_packet_received:
                    d[self.pid].n_packet_received += 1

                if need_n_packet_fragmented:
                    d[self.pid].n_time_sent += 1

                if need_better_display:
                    stdscr.addstr((self.pid*info_row), 0, "Device[{id}] received: {dat}".format(id=self.pid, dat=indata.hex()))
                    stdscr.refresh()
                #else:
                #    print("Device[{id}] received: {dat}".format(id=self.pid, dat=indata.hex()))


                if need_n_packet_received:
                    if need_better_display:
                        stdscr.addstr((self.pid * info_row + 1), 0, "Device[{id}] have received {n} packets".format(id=self.pid, n=d[self.pid].n_packet_received))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] have received {n} packets".format(id=self.pid, n=d[self.pid].n_packet_received))

                if need_n_corrupt:
                    if need_better_display:
                        stdscr.addstr((self.pid*info_row+2), 0, "Device[{id}] have received {n} corrupted packets".format(id=self.pid, n=d[self.pid].error_count))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] have received {n} corrupted packets".format(id=self.pid, n=d[self.pid].error_count))

                if need_n_packet_fragmented:
                    if need_better_display:
                        #stdscr.addstr((self.pid*info_row+3), 0, "Device[{id}] have detected {n} fragmented packets".format(id=self.pid, n=d[self.pid].n_time_received-d[self.pid].n_time_sent+d[self.pid].n_fragment))
                        stdscr.addstr((self.pid*info_row+2), 0, "Device[{id}] have detected {n} fragmented packets".format(id=self.pid, n=d[self.pid].n_fragment))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] have detected {n} fragmented packets".format(id=self.pid, n=d[self.pid].n_time_received-d[self.pid].n_time_sent+d[self.pid].n_fragment))

                if need_n_packet_loss:
                    if need_better_display:
                        stdscr.addstr((self.pid*info_row+4), 0, "Device[{id}] have {n} packets loss".format(id=self.pid, n=d[self.pid].n_packet_loss))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] have {n} packets loss".format(id=self.pid, n=d[self.pid].n_packet_loss))

                if need_elapsed_time:
                    if need_better_display:
                        #stdscr.addstr((self.pid*info_row+5), 0, "Elapsed time: {time}".format(time=time.time()-d[self.pid].start_time))
                        stdscr.addstr((self.pid*info_row+3), 0, "Elapsed time: {time}".format(time=time.time()-d[self.pid].start_time))
                        stdscr.refresh()
                    #else:
                    #    print("Elapsed time: {time}".format(time=time.time()-d[self.pid].start_time))

                #if not self.pid == 2: #no ack for imu
                #    d[self.pid].ch.write(ACK)

            

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

    def is_completed(self):
        if self.acc_x + self.acc_y + self.acc_z == -3:
            return False
        if self.gyro_x + self.gyro_y + self.gyro_z == -3:
            return False
        return True

    def is_moving(self):
        if self.acc_x + self.acc_y + self.acc_z + self.gyro_x + self.gyro_y + self.gyro_z == 0:
            return False
        if not self.is_completed():
            raise SystemError
        return True


imu_indata = ImuData(-1)

def writeToFile(indata):
    global imu_indata, file_index, is_movement_detected, file_name, file_length
    if imu_indata.id != indata[1]:
        imu_indata = ImuData(indata[1])


    if indata[0] == 6:
        imu_indata.timestamp = struct.unpack('>L', indata[3:7])[0]
        imu_indata.acc_x = struct.unpack('>h', indata[7:9])[0]
        imu_indata.acc_y = struct.unpack('>h', indata[9:11])[0]
        imu_indata.acc_z = struct.unpack('>h', indata[11:13])[0]
        imu_indata.gyro_x = struct.unpack('>h', indata[13:15])[0]
        imu_indata.gyro_y = struct.unpack('>h', indata[15:17])[0]
        imu_indata.gyro_z = struct.unpack('>h', indata[17:19])[0]
        
    if imu_indata.is_completed():
        imu_filename = f"""./data/{file_name}_{file_index}.csv"""
        if imu_indata.is_moving():
            is_movement_detected = True
            file_length = file_length + 1
            with open(imu_filename, "a") as f:
                f.write(f"""{imu_indata.timestamp},{ACTION_NUM},{imu_indata.acc_x},{imu_indata.acc_y},{imu_indata.acc_z},{imu_indata.gyro_x},{imu_indata.gyro_y},{imu_indata.gyro_z}\n""")
                f.close()
'''
        else:
            if is_movement_detected:
                if file_length >= 15:
                    print(f"""{imu_filename} saved""")
                    file_index = file_index + 1
                else:
                    file_length = 0
                    with open(imu_filename, "w") as f:
                        f.write("")
                        f.close()
                file_length = 0
            is_movement_detected = False
'''


def reorderData(data):
    '''
    #|01|01|01|67452301|67452301|67452301|01|01|01|01|01|
    tempdata = data[3:15]
    data[3] = tempdata[3]
    data[4] = tempdata[2]
    data[5] = tempdata[1]
    data[6] = tempdata[0]
    data[7] = tempdata[7]
    data[8] = tempdata[6]
    data[9] = tempdata[5]
    data[10] = tempdata[4]
    data[11] = tempdata[11]
    data[12] = tempdata[10]
    data[13] = tempdata[9]
    data[14] = tempdata[8]
    '''

    # |01|01|01|67452301|2301|2301|2301|2301|2301|2301|01|
    tempdata = data[3:19]
    data[3] = tempdata[3]
    data[4] = tempdata[2]
    data[5] = tempdata[1]
    data[6] = tempdata[0]
    data[7] = tempdata[5]
    data[8] = tempdata[4]
    data[9] = tempdata[7]
    data[10] = tempdata[6]
    data[11] = tempdata[9]
    data[12] = tempdata[8]
    data[13] = tempdata[11]
    data[14] = tempdata[10]
    data[15] = tempdata[13]
    data[16] = tempdata[12]
    data[17] = tempdata[15]
    data[18] = tempdata[14]

def verifyValidData(data):
    #if not (data[0] == 4 or data[0] == 5 or data[0] == 6 or data[0] == 22):
    if not (data[0] == 4 or data[0] == 5 or data[0] == 6):
        return False
    else:
        sum = 0
        for x in range(19):
            try:
                sum ^= int.from_bytes(data[x], 'big')
            except TypeError:
                sum ^= data[x]

        try:
            if sum == int.from_bytes(data[19], 'big'):
                return True
            else:
                print("WRONG CHECKSUM")
                return False
        except TypeError:
            if sum == data[19]:
                return True
            else:
                print("WRONG CHECKSUM")
                return False


def handleBeetle(i):
    d.append(PeripheralInfo())
    d[i].peripheral = btle.Peripheral()
    d[i].data = bytearray(b'')
    if need_better_display:
        stdscr.addstr((i*info_row), 0, "Connecting device {id}".format(id=i))
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
            stdscr.addstr((i*info_row), 0, "Device[{id}] connected".format(id=i))
            stdscr.refresh()
        else:
            print("Device[{id}] connected".format(id=i))
    except btle.BTLEDisconnectError:
        if need_better_display:
            stdscr.addstr((i*info_row), 0, "Device[{id}] not connected".format(id=i))
            stdscr.refresh()
        else:
            print("Device[{id}] not connected".format(id=i))
    except AttributeError:
        if need_better_display:
            stdscr.addstr((i*info_row), 0, "Device[{id}] not connected".format(id=i))
            stdscr.refresh()
        else:
            print("Device[{id}] not connected".format(id=i))
        time.sleep(1)

    while True:
        try:
            if d[i].setup == 0: #check setup
                if need_better_display:
                    stdscr.addstr((i*info_row), 0, "Try setting up device[{id}] again".format(id=i))
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
                        stdscr.addstr((i*info_row), 0, "Device[{id}] connected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] connected".format(id=i))
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr((i*info_row), 0, "Device[{id}] still not connected".format(id=i))
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
            elif d[i].connection == 0: #check connection
                if need_better_display:
                    stdscr.addstr((i*info_row), 0, "Reconnecting device[{id}]                                      ".format(id=i))
                    stdscr.refresh()
                else:
                    print("Reconnecting device[{id}]".format(id=i))
                try:
                    d[i].peripheral.connect(mac[i])
                    d[i].connection = 1
                    d[i].handshake_start = 0
                    d[i].handshake_done = 0
                    if need_better_display:
                        stdscr.addstr((i*info_row), 0, "Device[{id}] connected   ".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] connected".format(id=i))
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr((i*info_row), 0, "Device[{id}] not connected".format(id=i))
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
                        stdscr.addstr((i*info_row), 0, "Device[{id}] begin handshake".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] begin handshake".format(id=i))
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr((i*info_row), 0, "Device[{id}] disconnected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] disconnected".format(id=i))
                    d[i].connection = 0
            elif d[i].handshake_done == 0:  # check handshake is done
                if need_better_display:
                    stdscr.addstr((i*info_row), 0, "Device[{id}] waiting handshake ACK...".format(id=i))
                    stdscr.refresh()
                else:
                    print("Device[{id}] waiting handshake ACK...".format(id=i))
                try:
                    d[i].peripheral.waitForNotifications(1.0)
                    if time.time() > timeout:
                        if need_better_display:
                            stdscr.addstr((i*info_row), 0, "Device[{id}] resend handshake".format(id=i))
                            stdscr.refresh()
                        else:
                            print("Device[{id}] resend handshake".format(id=i))
                        d[i].handshake_start = 0
                        d[i].handshake_done = 0
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr((i*info_row), 0, "Device[{id}] disconnected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] disconnected".format(id=i))
                    d[i].connection = 0
            else:  # normal communication
                #if need_better_display:
                #    '''
                #    stdscr.addstr(i, 0, "Device[{id}] waiting...".format(id=i))
                #    stdscr.clrtoeol()
                #    stdscr.refresh()
                #    '''
                #else:
                    #print("Device[{id}] waiting...".format(id=i))
                try:
                    d[i].peripheral.waitForNotifications(1.0)
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr((i*info_row), 0, "Device[{id}] disconnected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] disconnected".format(id=i))
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
                self.start_time = 0

            if need_n_packet_received:
                self.n_packet_received = 0

            if need_n_packet_fragmented:
                self.n_time_received = -1
                self.n_time_sent = 0

            if need_n_packet_loss:
                self.n_packet_loss = 0
                self.prev_msg_id = 0


if __name__ == "__main__":
    threads = list()

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

    '''
    if need_better_display:
        t = threading.Thread(target=handleDisplay)
        threads.append(t)
    '''

    for t in threads:
        t.start()
