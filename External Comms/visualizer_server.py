import random
import time
import threading
from multiprocessing import Queue
import json
from queue import Empty

from paho.mqtt import client as mqtt_client

class visualizer_server(threading.Thread):
    def __init__(self, broker, port, topic, username, password, gamestate_queue):
        self.broker = broker
        self.port = port
        self.username = username
        self.topic = topic
        self.password = password
        self.client_id = f'ultra96-{random.randint(0, 1000)}'
        self.client = None
        self.gamestate = "hohoho"
        self.gamestate_queue = gamestate_queue

        threading.Thread.__init__(self)
        return

    #def run(self):

    def connect_mqtt(self):
        client = mqtt_client.Client(self.client_id)
        client.username_pw_set(self.username, self.password)
        client.connect(self.broker, self.port)
        return client


    def publish(self):
        while True:
            try: 
                self.gamestate = self.gamestate_queue.get()
                msg = json.dumps(self.gamestate)
            except Empty:
                msg = json.dumps(self.gamestate)

            result = self.client.publish(self.topic, msg)
            # result: [0, 1]
            
    def run(self):
        self.client = self.connect_mqtt()
        self.client.loop_start()
        print(self.client_id)
        self.publish()


if __name__ == '__main__':
    q = Queue()
    my_visualizer = visualizer_server(broker='broker.emqx.io'
                                        , port=1883
                                        , topic="ultra96"
                                        , username="KaiserHuang"
                                        , password="public"
                                        , gamestate_queue=q)
                                        
    my_visualizer.start()