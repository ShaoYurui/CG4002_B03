import random
import threading
import time

from paho.mqtt import client as mqtt_client
from queue import Empty
from multiprocessing import Queue

# sight_client Parameters
SIGHT_BROKER               = 'broker.emqx.io'
SIGHT_PORT                 = 1883
SIGHT_TOPIC                = "ultra96_reverse"
SIGHT_USERNAME             = "KaiserHuang"
SIGHT_PASSWORD             = "public"

class sight_client(threading.Thread):
    def __init__(self, broker, port, topic, username, password, sight_queue):
        self.broker = broker
        self.port = port
        self.username = username
        self.topic = topic
        self.password = password
        self.client_id = f'ultra96_reverse-{random.randint(0, 1000)}'
        self.sight_state = 0
        self.sight_queue = sight_queue
        self.count = 0

        threading.Thread.__init__(self)
        return

    def connect_mqtt(self) -> mqtt_client:
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(self.client_id)
        client.username_pw_set(self.username, self.password)
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        return client
    
    def subscribe(self, client: mqtt_client):

        def on_message(client, userdata, msg):
            if self.count == 0:
                print("First Connection")
                self.count += 1
            else: 
                self.sight_state = msg.payload.decode('utf-8')
                print("I DID THE JOB!")
                self.sight_queue.put(int(self.sight_state))
        
        client.subscribe(self.topic)
        client.on_message = on_message

    def run(self):
        client = self.connect_mqtt()
        self.subscribe(client)
        client.loop_forever()

if __name__ == '__main__':
    my_sight_queue = Queue()
    my_sight_client = sight_client(SIGHT_BROKER
                                    , SIGHT_PORT
                                    , SIGHT_TOPIC
                                    , SIGHT_USERNAME
                                    , SIGHT_PASSWORD
                                    , my_sight_queue)
    
    my_sight_client.start()
    my_sight_client.join()


"""
broker = 'broker.emqx.io'
port = 1883
topic = "ultra96_reverse"
# generate client ID with pub prefix randomly
client_id = f'ultra96_reverse-{random.randint(0, 100)}'
username = 'KaiserHuang'
password = 'public'


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()

"""
