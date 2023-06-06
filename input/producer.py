import asyncio
import os
import cv2

import numpy as np

from pathlib import Path
from fogverse import Producer
from fogverse.logging import CsvLogging
from fogverse.util import (get_cam_id, get_timestamp_str)

SIZE = (640,480)
DIR = Path('val2017')

class MyFrameProducer(CsvLogging, Producer):
    def __init__(self, loop=None):
        self.cam_id = get_cam_id()
        self.producer_topic = 'input'
        self.frame_idx = 1
        CsvLogging.__init__(self)
        Producer.__init__(self,loop=loop)

    def _after_start(self):
        with open('images.txt') as f:
            self.images_name = f.read().split(',')

    def _receive(self):
        img_name = self.images_name.pop(0)
        with open(str(DIR / img_name), 'rb') as f:
            data = f.read()
        return data

    async def receive(self):
        return await self._loop.run_in_executor(None, self._receive)

    def decode(self, data):
        nparr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, SIZE)
        return frame

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
    def __init__(self, loop=None):
        self.producer_servers = os.getenv('LOCAL_KAFKA')
        super().__init__(loop)

class MyFrameProducerSc3(MyFrameProducer):
    def __init__(self, loop=None):
        self.producer_servers = os.getenv('CLOUD_KAFKA')
        super().__init__(loop)


scenarios = {
    2: (MyFrameProducerSc2_4),
    3: (MyFrameProducerSc3),
    4: (MyFrameProducerSc2_4),
}

async def main():
    scenario = int(os.getenv('SCENARIO', 4))

    _Producer = scenarios[scenario]
    producer = _Producer()
    tasks = [producer.run()]
    try:
        await asyncio.gather(*tasks)
    except:
        for t in tasks:
            t.close()

if __name__ == '__main__':
    asyncio.run(main())
