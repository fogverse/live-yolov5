import numpy as np

from unittest import TestCase
from unittest.mock import MagicMock, patch

from fogverse.util import numpy_to_bytes

from .producer import MyProducer

class TestProducer(TestCase):
    @patch('cv2.VideoCapture')
    @patch('fogverse.consumer_producer._Producer')
    @patch('time.time')
    @patch('uuid.uuid4')
    @patch('fogverse.OpenCVConsumer.receive')
    @patch('fogverse.Runnable.close')
    def test_run(self, mock_runnable_close, mock_runnable_receive,
                          mock_uuid4, mock_time,
                          mock_kafka_prod, mock_cv2_vid):
        mock_producer = MagicMock()
        mock_kafka_prod.return_value = mock_producer

        cam_id = 1
        mock_uuid4.return_value = cam_id

        _time = 111
        mock_time.return_value = _time

        img = np.ones((10,20,3),dtype='uint8')
        mock_runnable_receive.side_effect = [img]

        acked = MagicMock()
        producer = MyProducer()
        producer.acked = acked
        producer.run()

        encoded_image = numpy_to_bytes(img)

        key = '1'
        headers = {
            'cam': f'cam_{cam_id}',
            'frame': '1',
            'timestamp': str(_time),
        }
        mock_producer.produce.assert_called_with('input',
                                           key=key,
                                           value=encoded_image,
                                           headers=headers,
                                           callback=acked)
        mock_runnable_close.assert_called_once()
