import os
import cv2
import numpy as np
import torch

from fogverse import ConsumerStorage, Producer
from threading import Thread

from fogverse.util import bytes_to_numpy, numpy_to_bytes

class MyConsumer(ConsumerStorage, Thread):
    def __init__(self, keep_messages=False):
        self.consumer_topic = ['input']
        ConsumerStorage.__init__(self, keep_messages=keep_messages)
        Thread.__init__(self)

class MyJetson(Producer):
    def __init__(self, consumer):
        MODEL = os.getenv('MODEL', 'yolov5n')
        self.model = torch.hub.load('ultralytics/yolov5', MODEL)
        self.producer_topic = 'result'
        self.consumer = consumer
        super().__init__()

    def receive(self):
        return self.consumer.get()

    def decode(self, data):
        self.message = data['message']
        return super().decode(data['data'])

    def process(self, preprocessed):
        results = self.model(preprocessed)
        return results.render()[0]

    def encode(self, img):
        _, encoded = cv2.imencode('.jpg', img)
        return numpy_to_bytes(encoded)

    def send(self, data):
        headers = {**self.message.headers(),
                    'type': 'final'}
        super().send(data, headers=headers)

if __name__ == '__main__':
    consumer = MyConsumer()
    inference = MyJetson(consumer)
    consumer.start()
    inference.run()
