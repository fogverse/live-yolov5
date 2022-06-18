import asyncio
import bisect
import os
import uuid

from fogverse import ConsumerStorage, Producer, Consumer
from fogverse.util import (
    calc_datetime, get_timestamp, get_timestamp_str, timestamp_to_datetime
)
from util import (
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

class MyConsumerStorage(Consumer, ConsumerStorage):
    def __init__(self):
        self.consumer_topic = ['input', 'result']
        self.consumer_conf = {'group_id': str(uuid.uuid4())}
        self.auto_encode = False
        self._data = {}
        Consumer.__init__(self)
        ConsumerStorage.__init__(self)

    def get_data(self):
        return self._data

    def _after_receive(self, data):
        super()._after_receive(data)
        headers = {key: value for key, value in data.headers}
        data.headers = headers
        cam_id = headers['cam'].decode()
        self._data.setdefault(cam_id, {
            'last_frame_idx': -1,
            'timestamp': get_timestamp_str(),
            'data': [],
            'max_delay': -1,
            'max_delay_frame': -1,
        })

        if data.topic == 'input': return data
        return data

    def decode(self, data):
        headers = self.message.headers
        if headers is not None:
            self.message.headers = {**headers,
                'frame': int(headers['frame']),
                'timestamp': timestamp_to_datetime(headers['timestamp']),
                'cam': headers['cam'].decode(),
                'type': headers.get('type', b'').decode()}
        return super().decode(data)

    def process(self, data):
        headers = self.message.headers
        data_type = headers.get('type')
        if self.message.topic == 'input':
            data = compress_encoding(data, ENCODING)
        elif data_type == 'final':
            data = numpy_to_base64_url(data, 'jpg')
        self.message.value = ''
        return data

    def on_input_send(self, data, cam_id, frame_idx):
        last_frame_idx = self._data[cam_id]['last_frame_idx']
        if last_frame_idx != -1 and frame_idx <= last_frame_idx:
            return
        lst_data = self._data[cam_id]['data']
        idx = bisect.bisect_left(KeyWrapper(lst_data,
                                lambda x: x['message'].headers['frame']),
                                frame_idx)
        # print(f'input for frame {frame_idx}')
        obj = {
            'message': self.message,
            'data': data,
            'input_timestamp': get_timestamp(),
            'final_timestamp': -1,
            'delay': 0,
            'type': 'input',
            'from': 'input'
        }
        lst_data.insert(idx, obj)

    def on_inference_send(self, pred, cam_id, frame_idx):
        cam_data = self._data[cam_id]
        lst_data = cam_data['data']
        for _data in lst_data:
            if _data['message'].headers['frame'] != frame_idx: continue
            frame = recover_encoding(_data['data'])
            frame = box_label(pred, frame)
            # print(f'inference for frame {frame_idx}')
            _delay = calc_datetime(_data['input_timestamp'])
            _data['delay'] = _delay
            _data['final_timestamp'] = get_timestamp()
            if _delay > cam_data['max_delay']:
                cam_data['max_delay'] = max(cam_data['max_delay'],_delay)
                cam_data['max_delay_frame'] = frame_idx
            _data['data'] = numpy_to_base64_url(frame, ENCODING)
            _data['message'].headers = self.message.headers
            _data['type'] = 'final'
            _data['from'] = 'inference'

    def on_final_send(self, data, cam_id ,frame_idx):
        cam_data = self._data[cam_id]
        lst_data = cam_data['data']
        for _data in lst_data:
            if _data['message'].headers['frame'] != frame_idx: continue
            # print(f'jetson for frame {frame_idx}')
            _delay = calc_datetime(_data['input_timestamp'])
            _data['delay'] = _delay
            _data['final_timestamp'] = get_timestamp()
            if _delay > cam_data['max_delay']:
                cam_data['max_delay'] = max(cam_data['max_delay'],_delay)
                cam_data['max_delay_frame'] = frame_idx
            _data['data'] = data
            _data['message'].headers = self.message.headers
            _data['type'] = 'final'
            _data['from'] = 'jetson'

    async def send(self, data):
        headers = self.message.headers
        data_type = headers.get('type')
        cam_id = headers['cam']
        frame_idx = headers['frame']
        if self.message.topic == 'input':
            self.on_input_send(data, cam_id, frame_idx)
        elif data_type == 'inference':
            self.on_inference_send(data, cam_id, frame_idx)
        elif data_type == 'final':
            self.on_final_send(data, cam_id, frame_idx)

def print_message(message):
    indent = ' '*2
    for cam_id, cam_data in message.items():
        print(f'{cam_id}:')
        for attr_cam, value_cam in cam_data.items():
            if attr_cam == 'data':
                for msg in value_cam:
                    _type = msg.get('type')
                    _frame = msg['message'].headers['frame']
                    _input_timestamp = msg.get('input_timestamp')
                    _final_timestamp = msg.get('final_timestamp')
                    _delay = msg.get('delay')
                    _from = msg.get('from')
                    print(f'{indent*2}- type: {_type}')
                    print(f'{indent*2}  frame: {_frame}')
                    print(f'{indent*2}  input timestamp: {_input_timestamp}')
                    print(f'{indent*2}  final timestamp: {_final_timestamp}')
                    # print(f'{indent*2}  delay: {_delay}')
                    # print(f'{indent*2}  from: {_from}')
            else:
                print(f'{indent}{attr_cam}: {value_cam}')

def print_send_data(send_data):
    indent = ' '*2
    for cam_id, cam_data in send_data.items():
        print(f'{cam_id}:')
        for attr_cam, value_cam in cam_data.items():
            if attr_cam == 'data':
                print(f'{indent}data:')
                for msg in value_cam:
                    headers = msg['headers']
                    _frame = headers['frame']
                    print(f'{indent*2}  frame: {_frame}')
            else:
                print(f'{indent}{attr_cam}: {value_cam}')


class MyProducer(Producer):
    def __init__(self, consumer_storage, loop=None):
        self.consumer = consumer_storage
        self.auto_decode = False
        self.auto_encode = False
        self.avg_delay = 0
        self.n_avg_delay = 0
        self.thresh = os.getenv('WAIT_THRESH', 2000)
        self._loop = loop or asyncio.get_event_loop()
        Producer.__init__(self)

    @property
    def data(self):
        return self.consumer.get_data()

    async def receive(self):
        data = self.data
        await asyncio.sleep(self.thresh / 1e3)
        return data

    async def send(self, data):
        return data

    def process(self, *args):
        send_data = {}
        for cam_id, cam_data in self.message.items():
            if len(cam_data['data']) == 0: continue
            elapsed = calc_datetime(cam_data['timestamp'])
            if elapsed < self.thresh: continue
            frames = cam_data['data']
            send_frames = [{
                    'data': i['data'],
                    'headers': i['message'].headers}
                for i in frames if i['type'] == 'final']
            if len(send_frames) == 0: continue
            avg_delay = self.thresh / len(send_frames)
            self.avg_delay = (self.avg_delay * self.n_avg_delay + avg_delay) \
                / (self.n_avg_delay + 1)
            self.n_avg_delay += 1
            send_data[cam_id] = {
                'avg_delay': avg_delay,
                'data': send_frames,
            }
            if frames:
                cam_data['last_frame_idx'] = \
                    frames[-1]['message'].headers['frame']
            cam_data['data'] = []
            cam_data['timestamp'] = get_timestamp()
        return send_data

    def _send(self, cam_id, data, headers):
        topic = f'final_{cam_id}'
        task = super().send(data.encode(), topic=topic, headers=headers)
        self._loop.create_task(task)

    async def send(self, data):
        print_send_data(data)
        print(self.avg_delay)
        if not data: return
        for cam_id, cam_data in data.items():
            delay = cam_data['avg_delay']
            for i in range(len(cam_data['data'])):
                frames = cam_data['data'][i]
                headers = frames['headers']
                headers = [
                    ('cam', headers.get('cam', '').encode()),
                    ('frame', str(headers.get('frame')).encode()),
                    ('timestamp', get_timestamp_str(
                        headers.get('timestamp')).encode()),
                    ('type', str(headers.get('type')).encode()),
                ]
                _data = frames['data']
                _delay = delay * (i+1) / 1e3
                self._loop.call_later(_delay, self._send, cam_id,
                                      _data, headers)

async def main():
    consumer = MyConsumerStorage()
    producer = MyProducer(consumer)
    tasks = [consumer.run(), producer.run()]
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
