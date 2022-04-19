import cv2
import numpy as np

from unittest import TestCase
from unittest.mock import MagicMock, patch

from fogverse.util import numpy_to_bytes

from .preprocess import MyPreprocess

class TestPreprocess(TestCase):
    def setUp(self) -> None:
        self.consumer = MagicMock()
        return super().setUp()

    @patch('fogverse.consumer_producer._Producer')
    @patch('fog.raspberrypi4.preprocess.MyPreprocess.receive')
    def test_run(self, mock_receive,  mock_kafka_producer):
        producer = MagicMock()
        mock_kafka_producer.return_value = producer
        img = np.ones((5,5,3),dtype='uint8')

        mock_headers = {
            'cam': 'cam_1',
            'frame': '1',
            'timestamp': '111',
        }
        message = MagicMock()
        message.headers.return_value = mock_headers
        message.key.return_value = 1

        acked = MagicMock()

        mock_obj = {
            'message': message,
            'data': numpy_to_bytes(img),
        }
        mock_receive.side_effect = [mock_obj]

        preprocess = MyPreprocess(self.consumer)
        preprocess.acked = acked
        preprocess.run()

        preprocessed = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        encoded_image = numpy_to_bytes(preprocessed)

        producer.produce.assert_called_with('preprocess',
                                            key=1,
                                            value=encoded_image,
                                            headers=mock_headers,
                                            callback=acked)
