import cv2
import os
import torch

import numpy as np

from fogverse import Producer, ConsumerStorage
from threading import Thread

class MyConsumer(ConsumerStorage, Thread):
    def __init__(self, keep_messages=False):
        self.consumer_topic = ['preprocess']
        ConsumerStorage.__init__(self, keep_messages)
        Thread.__init__(self)

class MyCloud(Producer):
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

    def process(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        results = self.model(img)
        preds = results.xyxyn[0].cpu().numpy().astype(object)
        preds = np.pad(preds, ((0,0),(0,1)), constant_values='none')
        names = results.names
        for i, pred in enumerate(preds):
            idx = int(pred[-2])
            pred[-2] = idx
            pred[-1] = names[idx]
            preds[i] = pred
        return preds

    def send(self, data):
        headers = {**self.message.headers(), 'type': 'inference'}
        super().send(data, headers=headers)

if __name__ == '__main__':
    consumer = MyConsumer()
    cloud = MyCloud(consumer)
    consumer.start()
    cloud.run()
