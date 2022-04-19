import base64
import cv2
import numpy as np
from fogverse.util import bytes_to_numpy, numpy_to_bytes

from utils.plots import Annotator, colors

def box_label(pred,img,show_label=True):
    """
    Make a box label for an image with
    given prediction [x0,y0,x1,y1,conf,index_label]
    and labels [label1,label2,...]
    :param list pred: an array of n predictions * prediction
        [x0,y0,x1,y1,conf,index_label]
    :param Image.Image/array img: the image for the prediction
    :param [str] labels: labels of prediction [label1,label2,...]
    :return: the labeled image
    """
    if np.ndim(pred) == 3:
        pred = pred[0]
    for p in pred:
        annotator = Annotator(img)
        box = tuple(p[:4])
        conf = p[4]
        c = int(p[5])
        label = p[-1]
        text = f'{label} {conf:.2f}'
        if show_label == False:
            text = ''
        annotator.box_label(box, text, colors(c, True))
    return annotator.result()

def _encode(img, encoding):
    _, encoded = cv2.imencode(f'.{encoding}', img)
    return encoded

def compress_encoding(img, encoding):
    encoded = _encode(img, encoding)
    return numpy_to_bytes(encoded)

def _decode(img):
    return cv2.imdecode(img, cv2.IMREAD_COLOR)

def recover_encoding(img_bytes):
    img = bytes_to_numpy(img_bytes)
    return _decode(img)

def numpy_to_base64_url(img, encoding):
    img = _encode(img, encoding)
    b64 = base64.b64encode(img).decode()
    return f'data:image/{encoding};base64,{b64}'
