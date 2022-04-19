import base64
import bisect
import math
import os
import time

from threading import Thread

from fogverse import Producer, Consumer
from fogverse.util import bytes_to_numpy
from .util import (
    box_label, compress_encoding, numpy_to_base64_url, recover_encoding
)

ENCODING = os.getenv('ENCODING', 'jpg')

class KeyWrapper:
    def __init__(self, iterable, key):
        self.it = iterable
        self.key = key

    def __getitem__(self, i):
        return self.key(self.it[i])

    def __len__(self):
        return len(self.it)

class MyConsumerStorage(Consumer):
    def __init__(self):
        self.consumer_topic = ['input']
        self.auto_encode = False
        self._data = {}
        self.start = -1
        self.delta = -1
        super().__init__()

    def on_error(self, err):
        pass
        # raise err

    def get_data(self):
        return self._data

    def receive(self):
        if self.start == -1:
            self.start = time.time()
        data = super().receive()
        if data is None: return None
        self.delta = (time.time() - self.start) * 1E3
        self.start = -1

        headers = data.headers()
        cam_id = headers['cam']
        self._data.setdefault(cam_id, {
            'n': 0,
            'avg_delay': 0,
            'timestamp': time.time(),
            'last_frame_idx': -1,
            'data': [],
        })

        if data.topic() == 'input': return data

        n = self._data[cam_id]['n']
        avg_delay = self._data[cam_id]['avg_delay']
        avg_delay = (avg_delay * n + self.delta) / (n + 1)
        self._data[cam_id]['avg_delay'] = avg_delay
        self._data[cam_id]['n'] += 1
        return data

    def decode(self, data):
        headers = self.message.headers()
        if headers is not None:
            self.message.set_headers({**headers,
                'frame': int(headers['frame']),
                'timestamp': int(headers['timestamp'])})
        return super().decode(data)

    def process(self, data):
        headers = self.message.headers()
        data_type = headers['type']
        if self.message.topic() == 'input':
            data = compress_encoding(data, ENCODING)
        elif data_type == 'final':
            data = numpy_to_base64_url(data, 'jpg')
        self.message.set_value('')
        return data

    def on_input_send(self, data, cam_id, frame_idx):
        last_frame_idx = self._data[cam_id]['last_frame_idx']
        if last_frame_idx != -1 and frame_idx < last_frame_idx:
            return
        lst_data = self._data[cam_id]['data']
        idx = bisect.bisect_left(KeyWrapper(lst_data,
                                lambda x: x['message'].headers()['frame']),
                                frame_idx)
        obj = {
            'message': self.message,
            'data': data,
            'type': 'input',
        }
        lst_data.insert(idx, obj)

    def on_inference_send(self, pred, cam_id, frame_idx):
        lst_data = self._data[cam_id]['data']
        for _data in lst_data:
            if _data['message'].headers()['frame'] != frame_idx: continue
            frame = recover_encoding(_data['data'])
            frame = box_label(pred, frame)
            _data['data'] = numpy_to_base64_url(frame, ENCODING)
            _data['type'] = 'final'

    def on_final_send(self, data, cam_id ,frame_idx):
        lst_data = self._data[cam_id]['data']
        for _data in lst_data:
            if _data['message'].headers()['frame'] != frame_idx: continue
            _data['data'] = data
            _data['type'] = 'final'

    def send(self, data):
        headers = self.message.headers()
        data_type = headers['type']
        cam_id = headers['cam']
        frame_idx = headers['frame']
        if self.message.topic() == 'input':
            self.on_input_send(data, cam_id, frame_idx)
        elif data_type == 'inference':
            self.on_inference_send(data, cam_id, frame_idx)
        elif data_type == 'final':
            self.on_final_send(data, cam_id, frame_idx)

class MyProducer(Producer):
    def __init__(self, consumer):
        self.consumer = consumer
        self.auto_decode = False
        self.auto_encode = False
        self.thresh = os.getenv('WAIT_THRESH', 350) * 1e3
        Producer.__init__(self)

    @property
    def data(self):
        return self.consumer.get_data()

    def receive(self):
        return self.data

    def process(self, *args):
        send_data = {}
        for cam_id, data in self.message.items():
            if len(data['data']) == 0: continue
            elapsed = (time.time() - data['timestamp'])*1e3
            if elapsed < self.thresh: continue
            avg_delay = data['avg_delay']
            num_frame = int(self.thresh // avg_delay) or 1
            send_frames =  data['data'][:num_frame]
            send_frames = [{
                'data': i['data'],
                'headers': i['message'].headers()}
                    for i in send_frames \
                    if i['type'] == 'final']
            send_data[cam_id] = {
                'avg_delay': avg_delay,
                'data': send_frames,
            }
            data['data'] = data['data'][num_frame:]
            self.data[cam_id]['last_frame_idx'] = \
                send_frames[-1]['headers']['frame']
            data['timestamp'] = time.time()
        if not send_data: return None
        return send_data

    def _send(self, data, cam_id):
        for frame in data['data']:
            avg_delay = data['avg_delay']
            time.sleep(avg_delay)
            topic = f'final_{cam_id}'
            headers = frame['headers']
            super().send(frame['data'], topic=topic, headers=headers)

    def send(self, data):
        if data is None: return
        for cam_id, _data in data.items():
            thread_send = Thread(target=self._send, args=(_data,cam_id))
            thread_send.start()

if __name__ == '__main__':
    consumer_storage = MyConsumerStorage()
    producer = MyProducer(consumer_storage)
    consumer_storage.start()
    producer.run()
