import os
import asyncio
import torch

from fogverse import Consumer, Producer, ConsumerStorage
from fogverse.logging.logging import CsvLogging
from fogverse.util import get_header, numpy_to_base64_url

ENCODING = os.getenv('ENCODING', 'jpg')

class MyStorage(Consumer, ConsumerStorage):
    def __init__(self, keep_messages=False):
        self.consumer_topic = ['input']
        Consumer.__init__(self)
        ConsumerStorage.__init__(self, keep_messages=keep_messages)

class MyJetson(CsvLogging, Producer):
    def __init__(self, consumer):
        MODEL = os.getenv('MODEL', 'yolov5n')
        self.model = torch.hub.load('ultralytics/yolov5', MODEL)
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
        return numpy_to_base64_url(img, ENCODING).encode()

    async def send(self, data):
        headers = list(self.message.headers)
        headers.append(('type',b'final'))
        await super().send(data, headers=headers)
# ======================================================================
class MyJetsonSc2(MyJetson):
    def __init__(self, consumer):
        super().__init__(consumer)

    async def send(self, data):
        headers = self.message.headers
        cam_id = get_header(headers, 'cam')
        self.producer_topic = f'final_{cam_id}'
        await super().send(data)
# ======================================================================
class MyJetsonSc4(MyJetson):
    def __init__(self, consumer):
        self.producer_topic = 'result'
        super().__init__(consumer)

scenarios = {
    2: (MyStorage, MyJetsonSc2),
    4: (MyStorage, MyJetsonSc4),
}

async def main():
    scenario = int(os.getenv('SCENARIO', 4))
    _Consumer, _Producer = scenarios[scenario]
    consumer = _Consumer()
    producer = _Producer(consumer)
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
