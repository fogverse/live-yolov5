import asyncio
import os
import uuid
import cv2

from datetime import datetime
import numpy as np

from fogverse import ConsumerStorage, Producer, OpenCVConsumer
from fogverse.logging import CsvLogging

rstate = np.random.RandomState(42)
# SIZE = (10,10,3)
# SIZE = (100,100,3)
SIZE = (480,640,3)
# SIZE = (1280,720,3)
# SIZE = (1080,1920,3)

class MyConsumer(OpenCVConsumer, ConsumerStorage):
    def __init__(self):
        OpenCVConsumer.__init__(self)
        ConsumerStorage.__init__(self)
        self.consumer.set(cv2.CAP_PROP_FRAME_WIDTH, SIZE[1])
        self.consumer.set(cv2.CAP_PROP_FRAME_HEIGHT, SIZE[0])

    def _receive(self):
        return rstate.randint(0,256,size=SIZE,dtype='uint8')

    async def receive(self):
        await asyncio.sleep(50 / 1e3)
        return await self._loop.run_in_executor(None, self._receive)

class MyInput(CsvLogging, Producer):
    def __init__(self, consumer, loop=None):
        self.consumer = consumer
        self.cam_id = f"cam_{os.getenv('CAM_ID', str(uuid.uuid4()))}"
        self.producer_topic = 'input'
        # self.producer_conf = {'max_request_size':10000000}
        self.frame_idx = 1
        CsvLogging.__init__(self)
        Producer.__init__(self,loop=loop)

    async def receive(self):
        return await self.consumer.get()

    async def send(self, data):
        key = str(self.frame_idx).encode()
        now = datetime.utcnow()
        strf = datetime.strftime(now, '%Y-%m-%d %H:%M:%S.%f')
        headers = [
            ('cam', self.cam_id.encode()),
            ('frame', str(self.frame_idx).encode()),
            ('timestamp', strf.encode())]
        await super().send(data, key=key, headers=headers)
        self.frame_idx += 1

async def main():
    consumer = MyConsumer()
    producer = MyInput(consumer)
    tasks = [consumer.run(), producer.run()]
    try:
        await asyncio.gather(*tasks)
    except:
        for t in tasks:
            t.close()

if __name__ == '__main__':
    asyncio.run(main())
