import cv2
import numpy as np

from unittest import TestCase
from unittest.mock import MagicMock, patch

from fogverse.util import numpy_to_bytes

from .inference import MyCloud

class TestCloud(TestCase):
    def setUp(self):
        self.consumer = MagicMock()
        return super().setUp()

    @patch('cloud.inference.torch.hub.load')
    @patch('fogverse.consumer_producer._Producer')
    @patch('cloud.inference.MyCloud.process')
    @patch('cloud.inference.MyCloud.receive')
    def test_run(self, mock_receive, mock_process, mock_kafka_producer,
                 mock_torch):
        inference_result = np.ones((7,6), dtype='uint8')
        mock_process.return_value = inference_result
        producer = MagicMock()
        mock_kafka_producer.return_value = producer
        img = np.ones((5,5),dtype='uint8')

        mock_headers = {
            'cam': 'cam_1',
            'frame': '1',
            'timestamp': '111',
            'type': 'inference',
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
        cloud = MyCloud(self.consumer)
        cloud.acked = acked
        cloud.run()

        inference_result_bytes = numpy_to_bytes(inference_result)
        producer.produce.assert_called_with('result',
                                            key=1,
                                            value=inference_result_bytes,
                                            headers=mock_headers,
                                            callback=acked)

