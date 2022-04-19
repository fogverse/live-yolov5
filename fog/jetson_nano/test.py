import cv2
import numpy as np

from unittest import TestCase
from unittest.mock import MagicMock, patch

from fogverse.util import numpy_to_bytes

from .inference import MyJetson

class TestPreprocess(TestCase):
    def setUp(self) -> None:
        self.consumer = MagicMock()
        return super().setUp()

    @patch('fog.jetson_nano.inference.torch.hub.load')
    @patch('fogverse.consumer_producer._Producer')
    @patch('fog.jetson_nano.inference.MyJetson.process')
    @patch('fog.jetson_nano.inference.MyJetson.receive')
    def test_run(self, mock_receive, mock_process, mock_kafka_producer,
                 mock_torch):
        img_result = np.ones((5,5,3),dtype='uint8')
        mock_process.return_value = img_result
        producer = MagicMock()
        mock_kafka_producer.return_value = producer
        img = np.ones((5,5,3),dtype='uint8')

        mock_headers = {
            'cam': 'cam_1',
            'frame': '1',
            'timestamp': '111',
            'type': 'final',
        }
        message = MagicMock()
        message.headers.return_value = mock_headers
        message.key.return_value = 1

        mock_obj = {
            'message': message,
            'data': numpy_to_bytes(img),
        }
        mock_receive.side_effect = [mock_obj]

        acked = MagicMock()
        jetson = MyJetson(self.consumer)
        jetson.acked = acked
        jetson.run()

        _, encoded = cv2.imencode('.jpg', img)
        encoded_image = numpy_to_bytes(encoded)

        producer.produce.assert_called_with('result',
                                            key=1,
                                            value=encoded_image,
                                            headers=mock_headers,
                                            callback=acked)
