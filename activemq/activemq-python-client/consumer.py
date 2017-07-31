# -*- coding:utf-8 -*-

import logging
from stompest.config import StompConfig
from stompest.protocol import StompSpec
from stompest.sync import Stomp

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

uri = 'failover:(tcp://x:61613,tcp://y:61613,tcp://z:61613)?randomize=false,startupMaxReconnectAttempts=3,initialReconnectDelay=7,maxReconnectDelay=8,maxReconnectAttempts=0'
CONFIG = StompConfig(uri)
QUEUE = '/queue/liuyang-test'

if __name__ == '__main__':
    client = Stomp(CONFIG)
    client.connect()
    client.subscribe(QUEUE, {StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL})
    while True:
        frame = client.receiveFrame()
        print('Got %s' % frame.info())
        client.ack(frame)
    client.disconnect()
