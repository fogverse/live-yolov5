import asyncio
import threading
import uuid

from fogverse import Consumer
from flask import Flask, render_template
from flask_socketio import SocketIO

from fogverse.logging import CsvLogging

def page_not_found(*args):
  return render_template('404.html'), 404

app = Flask(__name__)
app.register_error_handler(404, page_not_found)
socketio = SocketIO(app)

class MyClient(CsvLogging, Consumer):
    def __init__(self, socket: SocketIO, loop=None):
        self.socket = socket
        self.sockets = {}
        self.auto_encode = False
        self.topic_pattern = '^final_cam_[0-9a-zA-Z-]+$'
        self.consumer_conf = {'group_id': str(uuid.uuid4())}
        CsvLogging.__init__(self)
        Consumer.__init__(self,loop=loop)
        self.counter = 1

    async def send(self, data):
        topic = self.message.topic
        headers = self.message.headers
        headers = {key: value.decode() for key, value in headers}
        data = {
            'src': data,
            'headers': headers,
        }
        self.socket.emit(topic, data)

@app.route('/<cam_id>/')
def index(cam_id=None):
    if not cam_id:
        return page_not_found()
    return render_template('index.html')

async def main(loop):
    consumer = MyClient(socketio, loop=loop)
    tasks = [consumer.run()]
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()

def run_consumer(loop):
    try:
        loop.run_until_complete(main(loop))
    finally:
        loop.close()

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=run_consumer, args=(loop,))
    thread.start()
    socketio.run(app, debug=True, host='0.0.0.0', use_reloader=False)
