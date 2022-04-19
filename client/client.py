from time import time
import uuid
import base64
import cv2
import threading

import numpy as np

from fogverse import Consumer
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

class MyConsumer(Consumer, threading.Thread):
    def __init__(self):
        self.consumer_topic = ['input']
        self.auto_encode = False
        self.consumer_conf = {'group.id': str(uuid.uuid4())}
        Consumer.__init__(self)
        threading.Thread.__init__(self)

    def process(self, data):
        assert isinstance(data, np.ndarray), 'data should be in np.ndarray type'
        encoding = 'jpg'
        success, img_webp = cv2.imencode(f'.{encoding}', data)
        assert success, f'failed to encode image as {encoding}'
        b64_img = base64.b64encode(img_webp).decode()
        return f'data:image/{encoding};base64,{b64_img}'

    def send(self, data):
        socketio.emit('frame', {'data': data}, namespace='/video')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect', namespace='/video')
def on_connected(*args):
    emit('connected', namespace='/video')

if __name__ == '__main__':
    consumer = MyConsumer()
    consumer.start()
    socketio.run(app, debug=True, host='0.0.0.0', use_reloader=False)
