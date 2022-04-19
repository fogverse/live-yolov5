import cv2

from fogverse import ConsumerStorage, Producer
from threading import Thread

from fogverse.util import bytes_to_numpy

class MyConsumer(ConsumerStorage, Thread):
    def __init__(self, keep_messages=False):
        self.consumer_topic = ['input']
        ConsumerStorage.__init__(self, keep_messages=keep_messages)
        Thread.__init__(self)

class MyPreprocess(Producer):
    def __init__(self, consumer):
        self.producer_topic = 'preprocess'
        self.consumer = consumer
        super().__init__()

    def receive(self):
        return self.consumer.get()

    def decode(self, data):
        self.message = data['message']
        return bytes_to_numpy(data['data'])

    def process(self,data):
        return cv2.cvtColor(data, cv2.COLOR_RGB2GRAY)

if __name__ == '__main__':
    consumer = MyConsumer()
    fog = MyPreprocess(consumer)
    consumer.start()
    fog.start()
