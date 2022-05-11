from fogverse import Consumer, Producer

class MyForwarder(Consumer, Producer):
    def __init__(self):
        self.consumer_topic = ['result']
        self.producer_topic = ['result']
        Consumer.__init__(self)
        Producer.__init__(self)

if __name__ == '__main__':
    forwarder = MyForwarder()
    forwarder.run()
