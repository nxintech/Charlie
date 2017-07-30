import sys
import logging
from kafka import KafkaConsumer
from message_pb2 import Message

logger = logging.getLogger('kafka')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

message = Message()
consumer = KafkaConsumer('nginx-access-log',
                         value_deserializer=message.ParseFromString,
                         bootstrap_servers=['nxin-log-kafka01.test.yz:9092',
                                            'nxin-log-kafka02.test.yz:9092',
                                            'nxin-log-kafka03.test.yz:9092']
                         )
for msg in consumer:
    print(message.fields)
    break
