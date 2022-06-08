import asyncio
import cv2
import os
import torch

import numpy as np

from fogverse import Consumer, Producer, ConsumerStorage
from fogverse.logging.logging import CsvLogging

class MyConsumer(Consumer, ConsumerStorage):
    def __init__(self, keep_messages=False):
        self.consumer_topic = ['preprocess']
        Consumer.__init__(self)
        ConsumerStorage.__init__(self, keep_messages=keep_messages)

class MyCloud(CsvLogging, Producer):
    def __init__(self, consumer):
        MODEL = os.getenv('MODEL', 'yolov5n')
        self.model = torch.hub.load('ultralytics/yolov5', MODEL)
        self.producer_topic = 'result'
        self.consumer = consumer
        CsvLogging.__init__(self)
        Producer.__init__(self)

    async def receive(self):
        return await self.consumer.get()

    def _process(self, img):
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

    async def process(self, img):
        return await self._loop.run_in_executor(None,
                                               self._process,
                                               img)

    async def send(self, data):
        headers = list(self.message.headers)
        headers.append(('type',b'inference'))
        await super().send(data, headers=headers)

async def main():
    consumer = MyConsumer()
    producer = MyCloud(consumer)
    tasks = [consumer.run(), producer.run()]
    try:
        await asyncio.gather(*tasks)
    except:
        for t in tasks:
            t.close()

if __name__ == '__main__':
    asyncio.run(main())
