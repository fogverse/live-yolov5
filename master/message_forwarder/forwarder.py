import asyncio
import uuid

from fogverse import Consumer, Producer
from fogverse.logging import CsvLogging

class MyForwarder(CsvLogging, Consumer, Producer):
    def __init__(self):
        self.consumer_topic = ['result']
        self.consumer_conf = {'group_id': str(uuid.uuid4())}
        self.producer_topic = 'result'
        self.auto_decode = False
        self.auto_encode = False
        CsvLogging.__init__(self)
        Consumer.__init__(self)
        Producer.__init__(self)

async def main():
    forwarder = MyForwarder()
    tasks = [forwarder.run()]
    try:
        await asyncio.gather(*tasks)
    except:
        for t in tasks:
            t.close()

if __name__ == '__main__':
    asyncio.run(main())
