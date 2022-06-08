import os
import asyncio
import cv2
import torch

from fogverse import Consumer, Producer, ConsumerStorage
from fogverse.logging.logging import CsvLogging
from fogverse.util import numpy_to_bytes

class MyConsumer(Consumer, ConsumerStorage):
    def __init__(self, keep_messages=False):
        self.consumer_topic = ['input']
        Consumer.__init__(self)
        ConsumerStorage.__init__(self, keep_messages=keep_messages)

class MyJetson(CsvLogging, Producer):
    def __init__(self, consumer):
        MODEL = os.getenv('MODEL', 'yolov5n')
        self.model = torch.hub.load('ultralytics/yolov5', MODEL)
        self.producer_topic = 'result'
        self.consumer = consumer
        CsvLogging.__init__(self)
        Producer.__init__(self)

    async def receive(self):
        return await self.consumer.get()

    def _process(self, data):
        results = self.model(data)
        return results.render()[0]

    async def process(self, data):
        return await self._loop.run_in_executor(None,
                                               self._process,
                                               data)

    def encode(self, img):
        _, encoded = cv2.imencode('.jpg', img)
        return numpy_to_bytes(encoded)

    async def send(self, data):
        headers = list(self.message.headers)
        headers.append(('type',b'final'))
        await super().send(data, headers=headers)

async def main():
    consumer = MyConsumer()
    producer = MyJetson(consumer)
    tasks = [consumer.run(), producer.run()]
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
