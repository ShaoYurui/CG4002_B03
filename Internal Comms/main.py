from bluepy import btle

import threading
import time

#for debugging purpose
need_elapsed_time = True
need_n_packet_received = True
need_n_packet_fragmented = False
need_n_packet_loss = False
need_n_corrupt = False
need_better_display = True
need_write_to_file = False

if need_better_display:
    import curses

if need_write_to_file:
    import struct

ACK = b'\x41'
NAK = b'\x4E'

REQUEST_H = b'\x48'
ACK_H = b'\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x40'

nBeetle = 3

mac = list()
#mac.append('80:30:dc:d9:1f:93') # gun x
mac.append('34:14:b5:51:d9:04') # gun
#mac.append('34:15:13:22:a1:37') # vest x
mac.append('80:30:dc:d9:23:27') # vest
#mac.append('80:30:dc:e9:1c:74') # imu X
mac.append('80:30:dc:e9:08:d7') # imu

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

        buf_len = 20
        if self.pid == 2:
            buf_len = 40
        if len(d[self.pid].data) >= buf_len:
            indata = d[self.pid].data[0:20]
            #d[self.pid].data = d[self.pid].data[20:] # handled later

            d[self.pid].handshake_done = 1
            if indata == ACK_H:
                if need_better_display:
                    stdscr.addstr((self.pid * info_row), 0, "Device[{id}] handshake ACK received".format(id=self.pid))
                    stdscr.refresh()
                else:
                    print("Device[{id}] handshake ACK received".format(id=self.pid))
                # d[self.pid].ch.write(ACK)
                if not self.pid == 2:  # no ack for imu
                    d[self.pid].ch.write(ACK)

                if need_elapsed_time:
                    if d[self.pid].start_time == 0:
                        d[self.pid].start_time = time.time()

                d[self.pid].data = d[self.pid].data[20:]
            else:
                #reorderData(indata)
                if not verifyValidData(self.pid):
                    indata = d[self.pid].data[0:20]
                    if not need_better_display:
                        print("Device[{id}] received invalid data".format(id=self.pid))
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

                if need_n_packet_received:
                    d[self.pid].n_packet_received += 1

                if need_n_packet_fragmented:
                    d[self.pid].n_time_sent += 1

                if need_better_display:
                    stdscr.addstr((self.pid*info_row), 0, "Device[{id}] received: {dat}".format(id=self.pid, dat=indata.hex()))
                    stdscr.refresh()
                else:
                    print("Device[{id}] received: {dat}".format(id=self.pid, dat=indata.hex()))


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
                    else:
                        print("Elapsed time: {time}".format(time=time.time()-d[self.pid].start_time))

                if not self.pid == 2: #no ack for imu
                    d[self.pid].ch.write(ACK)

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


def reorderData(data):
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


def verifyValidData(id):
    #check & move to correct header
    header_index = 0
    if not ((d[id].data[header_index] == 4 or d[id].data[header_index] == 5 or d[id].data[header_index] == 6) and (d[id].data[header_index+2] == 1 or d[id].data[header_index+2] == 2)):
        #print("Header not correct: {header}".format(header=d[id].data[header_index]))
        for x in range(len(d[id].data)):
            #print("Index {index}: {databyte}, {databyte2}".format(index=x, databyte=d[id].data[x], databyte2=d[id].data[x+2]))
            if d[id].data[x] == 6 and (d[id].data[x+2] == 1 or d[id].data[x+2] == 2):
                header_index = x
                d[id].data = d[id].data[header_index:]
                #print("Found header at {index}".format(index=x))
                break
        if len(d[id].data) < 20:
            return False

    #verify checksum, return True if correct
    sum = 0
    #print("Data: {arrayobyte}".format(arrayobyte=d[id].data[0:20]))
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
    #print("Calculated checksum: {calcs}".format(calcs=sum))

    #(if checksum wrong) move to next header, return False
    #print("Try to find another header")
    for x in range(1, len(d[id].data)):
        #print("Index {index}: {databyte}, {databyte2}".format(index=x, databyte=d[id].data[x], databyte2=d[id].data[x+2]))
        if d[id].data[x] == 6 and (d[id].data[x + 2] == 1 or d[id].data[x + 2] == 2):
            #print("Found another header at {index}".format(index=x))
            header_index = x
            d[id].data = d[id].data[header_index:]
            #return False #return now, will handle data in next function call
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
            '''
            if need_n_corrupt:
                if d[i].error_count >= 5:
                    print("Device[%d] have received more than 5 corrupted packets, restarting" % i)
                    d[i].peripheral.disconnect()
                    d[i].svc = 0
                    d[i].ch = 0
                    d[i].setup = 0
                    d[i].connection = 0
                    d[i].handshake_start = 0
                    d[i].handshake_done = 0
                    d[i].data = bytearray(b'')
                    d[i].error_count = 0
                    if need_elapsed_time:
                        self.start_time = 0
                    if need_n_packet_received:
                        self.n_packet_received = 0
                    if need_n_packet_fragmented:
                        self.n_time_received = -1  # don't count first packet (handshake ack)
                        self.n_time_sent = 0
                    if need_n_packet_loss:
                        self.n_packet_loss = 0
                        self.prev_msg_id = -1
            '''
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
                if need_better_display:
                    '''
                    stdscr.addstr(i, 0, "Device[{id}] waiting...".format(id=i))
                    stdscr.clrtoeol()
                    stdscr.refresh()
                    '''
                else:
                    print("Device[{id}] waiting...".format(id=i))
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
