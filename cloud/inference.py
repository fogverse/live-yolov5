import asyncio
import cv2
import os
import torch

import numpy as np

from fogverse import Consumer, Producer, ConsumerStorage
from fogverse.logging.logging import CsvLogging
from fogverse.util import get_header, numpy_to_base64_url

class MyStorage(Consumer, ConsumerStorage):
    def __init__(self, keep_messages=False):
        Consumer.__init__(self)
        ConsumerStorage.__init__(self, keep_messages=keep_messages)

class MyCloud(CsvLogging, Producer):
    def __init__(self, consumer):
        MODEL = os.getenv('MODEL', 'yolov5n')
        self.model = torch.hub.load('ultralytics/yolov5', MODEL)
        self.consumer = consumer
        CsvLogging.__init__(self)
        Producer.__init__(self)

    async def receive(self):
        return await self.consumer.get()

    async def process(self, img):
        return await self._loop.run_in_executor(None,
                                               self._process,
                                               img)
# ======================================================================
ENCODING = os.getenv('ENCODING', 'jpg')
class MyStorageSc3(MyStorage):
    def __init__(self, keep_messages=False):
        self.consumer_topic = ['input']
        super().__init__(keep_messages)

class MyCloudSc3(MyCloud):
    def __init__(self, consumer):
        super().__init__(consumer)

    def _process(self, data):
        results = self.model(data)
        return results.render()[0]

    def encode(self, img):
        return numpy_to_base64_url(img, ENCODING).encode()

    async def send(self, data):
        headers = list(self.message.headers)
        headers.append(('type',b'final'))
        headers.append(('from',b'cloud'))
        cam_id = get_header(headers, 'cam')
        self.producer_topic = f'final_{cam_id}'
        await super().send(data, headers=headers)
# ======================================================================
class MyStorageSc4(MyStorage):
    def __init__(self, keep_messages=False):
        self.consumer_topic = ['preprocess']
        super().__init__(keep_messages)

class MyCloudSc4(MyCloud):
    def __init__(self, consumer):
        self.producer_topic = 'result'
        super().__init__(consumer)

    def _process(self, img):
        if img.ndim == 2:
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

    async def send(self, data):
        headers = list(self.message.headers)
        headers.append(('type',b'inference'))
        await super().send(data, headers=headers)

scenarios = {
    3: (MyStorageSc3, MyCloudSc3),
    4: (MyStorageSc4, MyCloudSc4),
}

async def main():
    scenario = int(os.getenv('SCENARIO', 4))
    _Consumer, _Producer = scenarios[scenario]
    consumer = _Consumer()
    producer = _Producer(consumer)
    tasks = [consumer.run(), producer.run()]
    try:
        await asyncio.gather(*tasks)
    except:
        for t in tasks:
            t.close()

if __name__ == '__main__':
    asyncio.run(main())
