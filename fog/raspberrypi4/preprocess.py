import asyncio
import cv2

from fogverse import Consumer, Producer, ConsumerStorage
from fogverse.logging.logging import CsvLogging

class MyStorage(Consumer, ConsumerStorage):
    def __init__(self, keep_messages=False):
        self.consumer_topic = ['input']
        Consumer.__init__(self)
        ConsumerStorage.__init__(self, keep_messages=keep_messages)

class MyPreprocess(CsvLogging, Producer):
    def __init__(self, consumer):
        self.producer_topic = 'preprocess'
        self.consumer = consumer
        CsvLogging.__init__(self)
        Producer.__init__(self)

    async def receive(self):
        return await self.consumer.get()

    def _process(self,data):
        img_resized = cv2.resize(data, (480,640))
        return cv2.cvtColor(img_resized, cv2.COLOR_RGB2GRAY)

    async def process(self, data):
        return await self._loop.run_in_executor(None,
                                               self._process,
                                               data)

async def main():
    consumer = MyStorage()
    producer = MyPreprocess(consumer)
    tasks = [consumer.run(), producer.run()]
    try:
        await asyncio.gather(*tasks)
    except:
        for t in tasks:
            t.close()

if __name__ == '__main__':
    asyncio.run(main())
