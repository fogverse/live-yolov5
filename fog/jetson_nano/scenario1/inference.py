import asyncio
import os
import threading

import cv2
import torch

from fogverse import ConsumerStorage
from flask import Flask, render_template
from flask_socketio import SocketIO
from fogverse.base import AbstractConsumer, AbstractProducer

from fogverse.consumer_producer import OpenCVConsumer
from fogverse.general import Runnable
from fogverse.logging.logging import CsvLogging
from fogverse.util import get_cam_id, get_timestamp_str, numpy_to_base64_url

def page_not_found(e):
  return render_template('404.html'), 404

app = Flask(__name__)
app.register_error_handler(404, page_not_found)
socketio = SocketIO(app)

ENCODING = os.getenv('ENCODING', 'jpg')
SIZE = (640,480,3)

class MyStorageSc1(OpenCVConsumer, ConsumerStorage):
    def __init__(self, loop=None):
        OpenCVConsumer.__init__(self, loop=loop)
        ConsumerStorage.__init__(self)
        self.cam_id = get_cam_id()
        self.consumer.set(cv2.CAP_PROP_FRAME_WIDTH, SIZE[0])
        self.consumer.set(cv2.CAP_PROP_FRAME_HEIGHT, SIZE[1])

class MyJetsonSc1(CsvLogging, AbstractConsumer, AbstractProducer, Runnable):
    def __init__(self, consumer, socket: SocketIO, loop=None):
        self.cam_id = get_cam_id()
        MODEL = os.getenv('MODEL', 'yolov5n')
        self.model = torch.hub.load('ultralytics/yolov5', MODEL)
        self.consumer = consumer
        self.socket = socket
        self.auto_encode = False
        self.read_last = False
        self._loop = loop
        CsvLogging.__init__(self)
        self.frame_idx = 1

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
        return numpy_to_base64_url(img, ENCODING)

    async def send(self, url_b64):
        now = get_timestamp_str()
        headers = {
            'cam': self.cam_id,
            'frame': str(self.frame_idx),
            'timestamp': now,
            'type':'final',
            'from': 'jetson'}
        namespace = f'/final_{self.cam_id}'
        data = {
            'src': url_b64,
            'headers': headers,
        }
        self.socket.emit('frame', data, namespace=namespace)
        self.frame_idx += 1

@app.route('/<cam_id>/')
def index(cam_id=None):
    if not cam_id:
        return render_template('404.html')
    return render_template('index.html')

async def main(loop):
    consumer = MyStorageSc1(loop=loop)
    producer = MyJetsonSc1(consumer, socketio, loop=loop)
    tasks = [consumer.run(), producer.run()]
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()

def run_main(loop):
    try:
        loop.run_until_complete(main(loop))
    finally:
        loop.close()

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=run_main, args=(loop,))
    thread.start()
    socketio.run(app, debug=True, host='0.0.0.0', use_reloader=False)
