import cv2
import numpy as np

from unittest import TestCase, mock
from unittest.mock import MagicMock, patch

from fogverse.util import numpy_to_bytes
from master.inference_merger.util import compress_encoding, numpy_to_base64_url, recover_encoding

from .inference_merger import MyConsumerStorage, MyProducer

random_state = np.random.RandomState(42)

class TestConsumerStorage(TestCase):
    def setUp(self) -> None:
        self.img = np.ones((5,5,3), dtype='uint8')
        self.maxDiff = 1e6
        return super().setUp()

    @patch('fogverse.consumer_producer._Consumer')
    @patch('time.time')
    @patch('master.inference_merger.inference_merger.Consumer.receive')
    def test_receive(self, mock_receive, mock_time, mock_consumer):
        mock_time.side_effect = [0, 50, 51]
        message = MagicMock()
        message.headers.return_value = {
            'cam': 'cam_1',
        }
        mock_receive.return_value = message
        storage = MyConsumerStorage()
        storage.receive()

        self.assertDictEqual(storage.get_data(), {
            'cam_1': {
                'n': 1,
                'avg_delay': 50 * 1E3,
                'timestamp': 51,
                'last_frame_idx': -1,
                'data': [],
            }
        })

    @patch('fogverse.consumer_producer._Consumer')
    def test_decode(self, mock_consumer):
        message = MagicMock()
        headers = {'frame':'1', 'timestamp': '111', 'type':'inference'}
        message.headers.return_value = headers
        storage = MyConsumerStorage()
        storage.message = message
        result = storage.decode(numpy_to_bytes(self.img))
        self.assertTrue((result == self.img).all())
        message.set_headers.assert_called_once_with({**headers,
            'frame': int(headers['frame']),
            'timestamp': int(headers['timestamp'])})

    @patch('fogverse.consumer_producer._Consumer')
    def test_process_type_input(self, mock_consumer):
        message = MagicMock()
        message.headers.return_value = {'type':''}
        message.topic.return_value = 'input'

        storage = MyConsumerStorage()
        storage.message = message
        result = storage.process(self.img)

        self.assertEqual(result, compress_encoding(self.img, 'jpg'))

    @patch('fogverse.consumer_producer._Consumer')
    def test_process_type_final(self, mock_consumer):
        message = MagicMock()
        message.headers.return_value = {'type':'final'}
        message.topic.return_value = ''

        storage = MyConsumerStorage()
        storage.message = message
        result = storage.process(self.img)

        self.assertEqual(result, numpy_to_base64_url(self.img, 'jpg'))

    @patch('fogverse.consumer_producer._Consumer')
    def test_process_type_inference(self, mock_consumer):
        message = MagicMock()
        message.headers.return_value = {'type':'inference'}
        message.topic.return_value = ''

        storage = MyConsumerStorage()
        storage.message = message
        result = storage.process(self.img)

        self.assertTrue((result == self.img).all())

    @patch('fogverse.consumer_producer._Consumer')
    def test_send_type_input(self, mock_consumer):
        message = MagicMock()
        message.headers.return_value = {'type':'','frame':2,'cam': 'cam_1'}
        message.topic.return_value = 'input'

        data = compress_encoding(self.img, 'jpg')

        storage = MyConsumerStorage()
        storage.message = message
        _data = {
            'cam_1': {
                'n': 1,
                'avg_delay': 50 * 1E3,
                'timestamp': 51,
                'last_frame_idx': -1,
                'data': [],
            }
        }
        storage._data = _data
        storage.send(data)

        _data['cam_1']['data'].append({
            'message': message,
            'data': data,
            'type': 'input'
        })
        self.assertDictEqual(storage.get_data(), _data)

        message.headers.return_value = {'type':'','frame':1,'cam': 'cam_1'}
        storage.send(data)

        _data['cam_1']['data'].insert(0, {
            'message': message,
            'data': data,
            'type': 'input'
        })
        self.assertDictEqual(storage.get_data(), _data)

        message.headers.return_value = {'type':'','frame':3,'cam': 'cam_1'}
        storage.send(data)

        _data['cam_1']['data'].append({
            'message': message,
            'data': data,
            'type': 'input'
        })
        self.assertDictEqual(storage.get_data(), _data)

    @patch('fogverse.consumer_producer._Consumer')
    def test_send_type_input_lt_last_frame_idx(self, mock_consumer):
        message = MagicMock()
        message.headers.return_value = {'type':'','frame':4,'cam': 'cam_1'}
        message.topic.return_value = 'input'

        data = compress_encoding(self.img, 'jpg')

        storage = MyConsumerStorage()
        storage.message = message
        _data = {
            'cam_1': {
                'n': 1,
                'avg_delay': 50 * 1E3,
                'timestamp': 51,
                'last_frame_idx': 5,
                'data': [],
            }
        }
        storage._data = _data
        storage.send(data)

        self.assertDictEqual(storage.get_data(), _data)

    @patch('fogverse.consumer_producer._Consumer')
    @patch('master.inference_merger.inference_merger.box_label')
    def test_send_type_inference(self, mock_box_label, mock_consumer):
        input_message = MagicMock()
        input_message.headers.return_value = {
            'type':'input','frame':1,'cam': 'cam_1'}
        input_message.topic.return_value = ''

        _data = {
            'cam_1': {
                'n': 1,
                'avg_delay': 50 * 1E3,
                'timestamp': 51,
                'last_frame_idx': -1,
                'data': [{
                    'message': input_message,
                    'data': compress_encoding(self.img,'jpg'),
                    'type': 'input'
                }],
            }
        }

        message = MagicMock()
        message.headers.return_value = {
            'type':'inference','frame':1,'cam': 'cam_1'}
        message.topic.return_value = ''

        result_image = np.zeros((5,5,3), dtype='uint8')
        mock_box_label.return_value = result_image

        storage = MyConsumerStorage()
        storage.message = message
        storage._data = _data
        inference_data = np.ones((3,3), dtype='uint8')
        storage.send(inference_data)

        self.assertEqual(storage.get_data(), {
            'cam_1': {
                'n': 1,
                'avg_delay': 50 * 1E3,
                'timestamp': 51,
                'last_frame_idx': -1,
                'data': [{
                    'message': input_message,
                    'data': numpy_to_base64_url(result_image, 'jpg'),
                    'type': 'final'
                }],
            }
        })

    @patch('fogverse.consumer_producer._Consumer')
    def test_send_type_final(self, mock_consumer):
        input_message = MagicMock()
        input_message.headers.return_value = {
            'type':'input','frame':1,'cam': 'cam_1'}
        input_message.topic.return_value = ''

        _data = {
            'cam_1': {
                'n': 1,
                'avg_delay': 50 * 1E3,
                'timestamp': 51,
                'last_frame_idx': -1,
                'data': [{
                    'message': input_message,
                    'data': compress_encoding(self.img,'jpg'),
                    'type': 'input'
                }],
            }
        }

        message = MagicMock()
        message.headers.return_value = {
            'type':'final','frame':1,'cam': 'cam_1'}
        message.topic.return_value = ''

        storage = MyConsumerStorage()
        storage.message = message
        storage._data = _data
        image = np.zeros((5,5,3), dtype='uint8')
        result_image = numpy_to_base64_url(image, 'jpg')
        storage.send(result_image)

        self.assertEqual(storage.get_data(), {
            'cam_1': {
                'n': 1,
                'avg_delay': 50 * 1E3,
                'timestamp': 51,
                'last_frame_idx': -1,
                'data': [{
                    'message': input_message,
                    'data': result_image,
                    'type': 'final'
                }],
            }
        })

    @patch('fogverse.consumer_producer._Consumer')
    @patch('time.time')
    @patch('master.inference_merger.inference_merger.Consumer.receive')
    def test_run_type_input(self, mock_receive, mock_time, mock_consumer):
        message = MagicMock()
        message.headers.return_value = {
            'type':'',
            'frame':2,
            'cam': 'cam_1',
            'timestamp':'111'}
        message.topic.return_value = 'input'
        img = random_state.randint(0,5,(1,2,3), dtype='uint8')
        data = numpy_to_bytes(img)
        message.value.return_value = data

        mock_receive.side_effect = [message]
        mock_time.side_effect = [0, 50, 51, 52]

        storage = MyConsumerStorage()
        storage.run()
        _data = {
            'cam_1': {
                'n': 0,
                'avg_delay': 0,
                'timestamp': 51,
                'last_frame_idx': -1,
                'data': [{
                    'message': message,
                    'data': compress_encoding(img, 'jpg'),
                    'type': 'input'
                }],
            }
        }
        self.assertDictEqual(storage.get_data(), _data)

        mock_time.side_effect = [52, 92, 93]

        img = random_state.randint(0,5,(1,2,3), dtype='uint8')
        data = numpy_to_bytes(img)
        message = MagicMock()
        message.topic.return_value = 'input'
        message.value.return_value = data
        message.headers.return_value = {
            'type':'',
            'frame':1,
            'cam': 'cam_1',
            'timestamp':'111'}
        mock_receive.side_effect = [message]
        storage.run()

        _data['cam_1']['data'].insert(0, {
            'message': message,
            'data': compress_encoding(img, 'jpg'),
            'type': 'input'
        })
        self.assertDictEqual(storage.get_data(), _data)

    @patch('fogverse.consumer_producer._Consumer')
    @patch('time.time')
    @patch('master.inference_merger.inference_merger.box_label')
    @patch('master.inference_merger.inference_merger.Consumer.receive')
    def test_run_type_inference(self, mock_receive, mock_box_label,
                                mock_time, mock_consumer):
        input_message = MagicMock()
        input_message.headers.return_value = {
            'type':'',
            'frame':1,
            'cam': 'cam_1',
            'timestamp':'111'}
        input_message.topic.return_value = 'input'
        img = random_state.randint(0,5,(1,2,3), dtype='uint8')
        img_jpg = compress_encoding(img, 'jpg')

        storage = MyConsumerStorage()
        _data = {
            'cam_1': {
                'n': 0,
                'avg_delay': 0,
                'timestamp': 50,
                'last_frame_idx': -1,
                'data': [{
                    'message': input_message,
                    'data': img_jpg,
                    'type': 'input'
                }],
            }
        }
        storage._data = _data

        inference = random_state.randint(0,5,(7,6), dtype='uint8')
        result_img = random_state.randint(0,5,(1,2,3), dtype='uint8')

        message = MagicMock()
        message.topic.return_value = ''
        message.value.return_value = numpy_to_bytes(inference)
        message.headers.return_value = {
            'type':'inference',
            'frame':1,
            'cam': 'cam_1',
            'timestamp':'111'}
        mock_receive.side_effect = [message]
        mock_box_label.return_value = result_img
        mock_time.side_effect = [0, 50, 51, 52]
        storage.run()

        self.assertDictEqual(storage.get_data(), {
            'cam_1': {
                'n': 1,
                'avg_delay': 50 * 1E3,
                'timestamp': 50,
                'last_frame_idx': -1,
                'data': [{
                    'message': input_message,
                    'data': numpy_to_base64_url(result_img, 'jpg'),
                    'type': 'final'
                }],
            }
        })

    @patch('fogverse.consumer_producer._Consumer')
    @patch('time.time')
    @patch('master.inference_merger.inference_merger.box_label')
    @patch('master.inference_merger.inference_merger.Consumer.receive')
    def test_run_type_final(self, mock_receive, mock_box_label,
                                mock_time, mock_consumer):
        input_message = MagicMock()
        input_message.headers.return_value = {
            'type':'',
            'frame':1,
            'cam': 'cam_1',
            'timestamp':'111'}
        input_message.topic.return_value = 'input'
        img = random_state.randint(0,5,(1,2,3), dtype='uint8')
        img_jpg = compress_encoding(img, 'jpg')

        storage = MyConsumerStorage()
        _data = {
            'cam_1': {
                'n': 0,
                'avg_delay': 0,
                'timestamp': 50,
                'last_frame_idx': -1,
                'data': [{
                    'message': input_message,
                    'data': img_jpg,
                    'type': 'input'
                }],
            }
        }
        storage._data = _data

        result_img = random_state.randint(0,5,(1,2,3), dtype='uint8')
        _, result_jpg = cv2.imencode('.jpg', result_img)
        data = numpy_to_bytes(result_jpg)
        recovered = recover_encoding(data)

        message = MagicMock()
        message.topic.return_value = ''
        message.value.return_value = data
        message.headers.return_value = {
            'type':'final',
            'frame':1,
            'cam': 'cam_1',
            'timestamp':'111'}
        mock_receive.side_effect = [message]
        mock_box_label.return_value = result_img
        mock_time.side_effect = [0, 50, 51, 52]
        storage.run()

        self.assertDictEqual(storage.get_data(), {
            'cam_1': {
                'n': 1,
                'avg_delay': 50 * 1E3,
                'timestamp': 50,
                'last_frame_idx': -1,
                'data': [{
                    'message': input_message,
                    'data': numpy_to_base64_url(result_jpg, 'jpg'),
                    'type': 'final'
                }],
            }
        })

class TestProducer(TestCase):
    def setUp(self) -> None:
        self.storage = MagicMock()
        self.img = np.ones((5,5,3), dtype='uint8')
        return super().setUp()

    @patch('time.time')
    @patch('os.getenv')
    def test_process_less_than_thresh(self, mock_getenv, mock_time):
        mock_time.side_effect = [149]
        mock_getenv.return_value = 100
        final_message = MagicMock()
        message = {
            'cam_1': {
                'n': 1,
                'avg_delay': 50 * 1E3,
                'timestamp': 50,
                'last_frame_idx': -1,
                'data': [{
                    'message': final_message,
                    'data': numpy_to_base64_url(self.img, 'jpg'),
                    'type': 'final'
                }],
            }
        }
        producer = MyProducer(self.storage)
        producer.message = message
        result = producer.process()

        self.assertIsNone(result)

    @patch('time.time')
    @patch('os.getenv')
    def test_process_more_than_thresh(self, mock_getenv, mock_time):
        mock_time.side_effect = [150, 151]
        mock_getenv.return_value = 100
        data_img = numpy_to_base64_url(self.img, 'jpg')
        final_message = MagicMock()
        final_message.headers.return_value = {
            'frame': 1
        }
        data = [{
            'message': final_message,
            'data': data_img,
            'type': 'final'
        }]
        message = {
            'cam_1': {
                'n': 1,
                'avg_delay': 50 * 1E3,
                'timestamp': 50,
                'last_frame_idx': -1,
                'data': data,
            }
        }
        self.storage.get_data.return_value = message
        producer = MyProducer(self.storage)
        producer.message = message
        result = producer.process()

        self.assertDictEqual(result, {
            'cam_1': {
                'avg_delay': 50 * 1E3,
                'data': [{
                    'data': data_img,
                    'headers': final_message.headers()
                }]
            }
        })
        self.assertDictEqual(producer.data, {
            'cam_1': {
                'avg_delay': 50 * 1E3,
                'data': [],
                'last_frame_idx': 1,
                'n': 1,
                'timestamp': 151
            }
        })

    @patch('time.time')
    @patch('os.getenv')
    def test_process_more_than_1_data(self, mock_getenv, mock_time):
        mock_time.side_effect = [150, 151]
        mock_getenv.return_value = 100
        data_img = numpy_to_base64_url(self.img, 'jpg')
        final_message = MagicMock()
        final_message.headers.return_value = {
            'frame': 1
        }
        data = [{
            'message': final_message,
            'data': data_img,
            'type': 'final'
        },{
            'message': final_message,
            'data': data_img,
            'type': 'input'
        }]
        message = {
            'cam_1': {
                'n': 1,
                'avg_delay': 70 * 1E3,
                'timestamp': 50,
                'last_frame_idx': -1,
                'data': data,
            }
        }
        self.storage.get_data.return_value = message
        producer = MyProducer(self.storage)
        producer.message = message
        result = producer.process()

        self.assertDictEqual(result, {
            'cam_1': {
                'avg_delay': 70 * 1E3,
                'data': [{
                    'data': data_img,
                    'headers': final_message.headers()
                }]
            }
        })
        self.assertDictEqual(producer.data, {
            'cam_1': {
                'avg_delay': 70 * 1E3,
                'data': [{
                    'message': final_message,
                    'data': data_img,
                    'type': 'input'
                }],
                'last_frame_idx': 1,
                'n': 1,
                'timestamp': 151
            }
        })

    @patch('fogverse.consumer_producer._Producer')
    @patch('master.inference_merger.inference_merger.Thread')
    def test_send(self, mock_thread, mock_producer):
        data_img = numpy_to_base64_url(self.img, 'jpg')
        data = {
            'cam_1': {
                'avg_delay': 70 * 1E3,
                'data': [{
                    'data': data_img,
                    'headers': {}
                }]
            }
        }

        producer = MyProducer(self.storage)
        producer.send(data)

        mock_thread.assert_called_once_with(target=producer._send,
                                            args=(data['cam_1'], 'cam_1'))

    @patch('fogverse.consumer_producer._Producer')
    @patch('fogverse.KafkaProducer.send')
    @patch('time.sleep')
    def test__send(self, mock_sleep, mock_send, mock_producer):
        data_img = numpy_to_base64_url(self.img, 'jpg')
        data = {
            'avg_delay': 70 * 1E3,
            'data': [{
                'data': data_img,
                'headers': {}
            }]
        }

        producer = MyProducer(self.storage)
        producer._send(data, 'cam_1')

        mock_sleep.assert_called_once_with(70 * 1E3)
        mock_send.assert_called_once_with(data_img,
                                          topic='final_cam_1',
                                          headers={})

    @patch('fogverse.consumer_producer._Producer')
    @patch('time.sleep')
    @patch('os.getenv')
    @patch('time.time')
    @patch('master.inference_merger.inference_merger.Thread')
    def test_run(self, mock_thread, mock_time, mock_getenv, mock_sleep,
                mock_producer):
        mock_time.side_effect = [150, 151]
        mock_getenv.return_value = 100
        data_img = numpy_to_base64_url(self.img, 'jpg')
        final_message1 = MagicMock()
        final_message1.headers.return_value = {
            'frame': 1
        }
        final_message2 = MagicMock()
        final_message2.headers.return_value = {
            'frame': 2
        }
        final_message3 = MagicMock()
        final_message3.headers.return_value = {
            'frame': 3
        }
        data = [{
            'message': final_message1,
            'data': data_img,
            'type': 'final'
        },{
            'message': final_message2,
            'data': data_img,
            'type': 'final'
        },{
            'message': final_message3,
            'data': data_img,
            'type': 'input'
        }]
        message = {
            'cam_1': {
                'n': 1,
                'avg_delay': 50 * 1E3,
                'timestamp': 50,
                'last_frame_idx': -1,
                'data': data,
            }
        }
        self.storage.get_data.return_value = message
        producer = MyProducer(self.storage)
        producer.run()

        expected_data = {
            'cam_1': {
                'avg_delay': 50 * 1E3,
                'data': [{
                    'data': data_img,
                    'headers': {'frame': 1}
                },{
                    'data': data_img,
                    'headers': {'frame': 2}
                }]
            }
        }

        producer._send(expected_data['cam_1'], 'cam_1')

        mock_thread.assert_called_once_with(target=producer._send,
                                        args=(expected_data['cam_1'], 'cam_1'))
        self.assertListEqual(
            [
                mock.call(50 * 1E3),
                mock.call(50 * 1E3),
            ],
            mock_sleep.mock_calls
        )
