import asyncio
import os
import cv2

import numpy as np

from fogverse import ConsumerStorage, Producer, OpenCVConsumer
from fogverse.logging import CsvLogging
from fogverse.util import get_cam_id, get_timestamp_str

SIZE = (640,480,3)

class MyStorage(OpenCVConsumer, ConsumerStorage):
    def __init__(self):
        OpenCVConsumer.__init__(self)
        ConsumerStorage.__init__(self)
        self.consumer.set(cv2.CAP_PROP_FRAME_WIDTH, SIZE[0])
        self.consumer.set(cv2.CAP_PROP_FRAME_HEIGHT, SIZE[1])

class MyFrameProducer(CsvLogging, Producer):
    def __init__(self, consumer, loop=None):
        self.consumer = consumer
        self.cam_id = get_cam_id()
        self.producer_topic = 'input'
        # self.producer_conf = {'max_request_size':10000000}
        self.frame_idx = 1
        CsvLogging.__init__(self)
        Producer.__init__(self,loop=loop)

    async def receive(self):
        return await self.consumer.get()

    async def send(self, data):
        key = str(self.frame_idx).encode()
        headers = [
            ('cam', self.cam_id.encode()),
            ('frame', str(self.frame_idx).encode()),
            ('timestamp', get_timestamp_str().encode())]
        await super().send(data, key=key, headers=headers)
        self.frame_idx += 1
# ======================================================================
class MyFrameProducerSc2_4(MyFrameProducer):
    def __init__(self, consumer, loop=None):
        self.producer_servers = os.getenv('LOCAL_KAFKA')
        super().__init__(consumer, loop)

class MyFrameProducerSc3(MyFrameProducer):
    def __init__(self, consumer, loop=None):
        self.producer_servers = os.getenv('CLOUD_KAFKA')
        super().__init__(consumer, loop)

scenarios = {
    2: (MyStorage, MyFrameProducerSc2_4),
    3: (MyStorage, MyFrameProducerSc3),
    4: (MyStorage, MyFrameProducerSc2_4),
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
