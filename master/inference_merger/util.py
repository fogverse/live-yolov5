import numpy as np

from utils.plots import Annotator, colors

def box_label(pred,img,show_label=True,relative=False,inplace=False):
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
    if not inplace:
        img = img.copy()
    if len(pred) == 0: return img
    for p in pred:
        annotator = Annotator(img)
        box = tuple(p[:4])
        if relative:
            width = img.shape[1]
            height = img.shape[0]
            box = (box[0]*width, box[1]*height, box[2]*width, box[3]*height)
        conf = p[4]
        c = int(p[5])
        label = p[-1]
        text = f'{label} {conf:.2f}'
        if show_label == False:
            text = ''
        annotator.box_label(box, text, colors(c, True))
    if not inplace:
        return annotator.result()
