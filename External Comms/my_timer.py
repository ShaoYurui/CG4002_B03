import time


class my_timer:
    def __init__(self):
        self.start_time = -1

    def get_timer(self):
        if self.start_time == -1:
            return -1
        cur_time = time.time()
        return cur_time - self.start_time

    def start_timer(self):
        self.start_time = time.time()

    def stop_timer(self):
        self.start_time = -1