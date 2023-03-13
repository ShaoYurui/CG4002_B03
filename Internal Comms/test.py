from bluepy import btle

import threading
import time

#for debugging purpose
need_elapsed_time = False
need_n_packet_received = False
need_n_packet_fragmented = False
need_n_packet_loss = False
need_better_display = False

if need_better_display:
    import curses

ACK = b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
REQUEST_H = b'\x48'
ACK_H = b'\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x40'

nBeetle = 1

mac = list()
mac.append('80:30:dc:d9:23:27') # vest

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
        #self.error_count = 0

        if need_elapsed_time:
            self.start_time = 0

        if need_n_packet_received:
            self.n_packet_received = 0

        if need_n_packet_fragmented:
            self.n_time_received = -1 #don't count first packet (handshake ack)
            self.n_time_sent = 0

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

            if d[self.pid].handshake_done == 0:
                if data == ACK_H:
                    if need_better_display:
                        stdscr.addstr(self.pid, 0, "Device[{id}] handshake ACK received".format(id=self.pid))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] handshake ACK received".format(id=self.pid))
                    d[self.pid].handshake_done = 1
                    #d[self.pid].ch.write(ACK)

                    if need_elapsed_time:
                        d[self.pid].start_time = time.time()

                else:
                    if need_better_display:
                        stdscr.addstr(self.pid, 0, "Device[{id}] received something instead of handshake ACK: {dat}".format(id=self.pid, dat=indata.hex()))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] received something instead of handshake ACK: {dat}".format(id=self.pid, dat=indata.hex()))
                    d[self.pid].peripheral.disconnect()
                    d[self.pid].connection = 0
                    d[self.pid].handshake_start = 0
                    d[self.pid].handshake_done = 0
            else:
                if not verifyValidData(data):
                    if need_better_display:
                        stdscr.addstr(self.pid, 0, "Device[{id}] received invalid data".format(id=self.pid))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] received invalid data".format(id=self.pid))
                    #d[self.pid].error_count += 1
                else:
                    if need_n_packet_loss:
                        if d[self.pid].prev_msg_id == -1:
                            d[self.pid].prev_msg_id = indata[1]
                        else:
                            if indata[0] == 4 or indata[0] == 5:
                                if indata[1] == d[self.pid].prev_msg_id:
                                    d[self.pid].n_packet_loss += 1
                            elif indata[0] == 6 or indata[0] == 16:
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
                    stdscr.addstr(self.pid, 0, "Device[{id}] received: {dat}".format(id=self.pid, dat=indata.hex()))
                    stdscr.refresh()
                else:
                    print("Device[{id}] received: {dat}".format(id=self.pid, dat=indata.hex()))
                #if d[self.pid].error_count > 0:
                #    print("Device[{id}] have received {n} corrupted packets".format(id=self.pid, n=id[self.pid].error_count))

                if need_n_packet_received:
                    print("Device[{id}] have received {n} packets".format(id=self.pid, n=d[self.pid].n_packet_received))

                if need_n_packet_fragmented:
                    print("Device[{id}] have detected {n} fragmented packets".format(id=self.pid, n=d[self.pid].n_time_received-d[self.pid].n_time_sent))

                if need_n_packet_loss:
                    print("Device[{id}] have {n} packets loss".format(id=self.pid, n=d[self.pid].n_packet_loss))

                if need_elapsed_time:
                    print("Elapsed time: {time}".format(time=time.time()-d[self.pid].start_time))

                #if not self.pid == 2: #no ack for imu
                #    d[self.pid].ch.write(ACK)


def verifyValidData(data):
    if not (data[0] == 4 or data[0] == 5 or data[0] == 6 or data[0] == 16):
        return False
    else:
        sum = 0
        for x in range(18):
            try:
                sum ^= int.from_bytes(data[x], 'big')
            except TypeError:
                sum ^= data[x]

        try:
            if sum == int.from_bytes(data[19], 'big'):
                return True
            else:
                return False
        except TypeError:
            if sum == data[19]:
                return True
            else:
                return False


def handleBeetle(i):
    d.append(PeripheralInfo())
    d[i].peripheral = btle.Peripheral()
    d[i].data = bytearray(b'')
    if need_better_display:
        stdscr.addstr(i, 0, "Connecting device {id}".format(id=i))
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
            #d[i].display_message = "Device{id} connected".format(id=i)
            stdscr.addstr(i, 0, "Device[{id}] connected".format(id=i))
            stdscr.refresh()
        else:
            print("Device[{id}] connected".format(id=i))
    except btle.BTLEDisconnectError:
        if need_better_display:
            #d[i].display_message = "Device{id} not connected".format(id=i)
            stdscr.addstr(i, 0, "Device[{id}] not connected".format(id=i))
            stdscr.refresh()
        else:
            print("Device[{id}] not connected".format(id=i))

    while True:
        try:
            '''
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
                    stdscr.addstr(i, 0, "Try setting up device[{id}] again".format(id=i))
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
                        stdscr.addstr(i, 0, "Device[{id}] connected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] connected".format(id=i))
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr(i, 0, "Device[{id}] still not connected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] still not connected".format(id=i))
            elif d[i].connection == 0: #check connection
                if need_better_display:
                    stdscr.addstr(i, 0, "Reconnecting device[{id}]".format(id=i))
                    stdscr.refresh()
                else:
                    print("Reconnecting device[{id}]".format(id=i))
                try:
                    d[i].peripheral.connect(mac[i])
                    d[i].connection = 1
                    d[i].handshake_start = 0
                    d[i].handshake_done = 0
                    if need_better_display:
                        stdscr.addstr(i, 0, "Device[{id}] connected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] connected".format(id=i))
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr(i, 0, "Device[{id}] not connected".format(id=i))
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
                        stdscr.addstr(i, 0, "Device[{id}] begin handshake".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] begin handshake".format(id=i))
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr(i, 0, "Device[{id}] disconnected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] disconnected".format(id=i))
                    d[i].connection = 0
            elif d[i].handshake_done == 0:  # check handshake is done
                if need_better_display:
                    stdscr.addstr(i, 0, "Device[{id}] waiting handshake ACK...".format(id=i))
                    stdscr.refresh()
                else:
                    print("Device[{id}] waiting handshake ACK...".format(id=i))
                try:
                    d[i].peripheral.waitForNotifications(1.0)
                    if time.time() > timeout:
                        if need_better_display:
                            stdscr.addstr(i, 0, "Device[{id}] resend handshake".format(id=i))
                            stdscr.refresh()
                        else:
                            print("Device[{id}] resend handshake".format(id=i))
                        d[i].handshake_start = 0
                        d[i].handshake_done = 0
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr(i, 0, "Device[{id}] disconnected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] disconnected".format(id=i))
                    d[i].connection = 0
            else:  # normal communication
                time.sleep(5)
                # b10010100
                d[i].ch.write(b'\x94')
                print('94')
                time.sleep(5)
                # b10010010
                d[i].ch.write(b'\x92')
                print('92')
                time.sleep(5)
                # b10010000
                d[i].ch.write(b'\x90')
                print('90')
                time.sleep(5)
                # b10001110
                d[i].ch.write(b'\x8E')
                print('8e')
                time.sleep(100)

                '''
                if need_better_display:
                else:
                    print("Device[{id}] waiting...".format(id=i))
                try:
                    d[i].peripheral.waitForNotifications(1.0)
                except btle.BTLEDisconnectError:
                    if need_better_display:
                        stdscr.addstr(i, 0, "Device[{id}] disconnected".format(id=i))
                        stdscr.refresh()
                    else:
                        print("Device[{id}] disconnected".format(id=i))
                    d[i].connection = 0
                '''
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