import os
import time
import uuid

from fogverse import Producer
from fogverse import OpenCVConsumer


class MyProducer(OpenCVConsumer, Producer):
    def __init__(self):
        self.cam_id = f"cam_{os.getenv('CAM_ID', str(uuid.uuid4()))}"
        self.producer_topic = 'input'
        self.auto_decode = False
        OpenCVConsumer.__init__(self)
        Producer.__init__(self)
        self.frame_idx = 1

    def acked(self, err, msg):
        print(err)
        print(msg)

    def send(self, data):
        key = self.frame_idx
        headers = {
            'cam': self.cam_id,
            'frame': str(self.frame_idx),
            'timestamp': str(time.time()),
        }
        super().send(data, key=key, headers=headers)
        self.frame_idx += 1

if __name__ == '__main__':
    producer = MyProducer()
    producer.run()
