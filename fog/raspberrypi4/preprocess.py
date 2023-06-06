import asyncio
import cv2
import os

from fogverse import Consumer, Producer, ConsumerStorage
from fogverse.logging.logging import CsvLogging
from fogverse.util import compress_encoding, numpy_to_bytes

class MyStorage(Consumer, ConsumerStorage):
    def __init__(self, keep_messages=False):
        self.consumer_topic = ['input']
        Consumer.__init__(self)
        ConsumerStorage.__init__(self, keep_messages=keep_messages)

    async def _after_start(self, *args, **kwargs) -> None:
        print(self.__class__.__name__, 'ready')

class MyPreprocess(CsvLogging, Producer):
    def __init__(self, consumer, compress, compress_name):
        self.producer_topic = 'preprocess'
        self.consumer = consumer
        self.compress = compress
        self.compress_name = compress_name
        CsvLogging.__init__(self)
        Producer.__init__(self)

    async def _after_start(self, *args, **kwargs) -> None:
        res = super()._after_start(*args, **kwargs)
        print(self.__class__.__name__, 'ready')
        return res

    async def receive(self):
        return await self.consumer.get()

    def _process(self,data):
        encode_func = self.compress[0]
        if not encode_func: return super().encode(data)
        encoded = encode_func(data, *self.compress[1:])
        return encoded

    async def send(self, data):
        headers = list(self.message.headers)
        headers.append(('compress', self.compress_name.encode()))
        await super().send(data, headers=headers)

    async def process(self, data):
        return await self._loop.run_in_executor(None,
                                               self._process,
                                               data)

# ======================================================================

def process_grayscale(data, *args):
    processed = cv2.cvtColor(data, cv2.COLOR_RGB2GRAY)
    return numpy_to_bytes(processed)

processes = {
    'jpeg 50': [compress_encoding, 'jpg', (cv2.IMWRITE_JPEG_QUALITY, 50)],
    'jpeg 75': [compress_encoding, 'jpg', (cv2.IMWRITE_JPEG_QUALITY, 75)],
    'jpeg 95': [compress_encoding, 'jpg', (cv2.IMWRITE_JPEG_QUALITY, 95)],
    'jpeg 2000': [compress_encoding, 'jp2'],
    'grayscale': [process_grayscale],
    'original': [None]
}

async def main():
    compress_name = os.getenv('COMPRESSION', 'jpeg 50')
    compress = processes[compress_name]

    consumer = MyStorage()
    producer = MyPreprocess(consumer, compress, compress_name)
    tasks = [consumer.run(), producer.run()]
    try:
        await asyncio.gather(*tasks)
    except:
        for t in tasks:
            t.close()

if __name__ == '__main__':
    asyncio.run(main())
