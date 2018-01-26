import sys
import logging
import threading
import requests
import ipaddress
from flask import Flask, Response
from user_agents import parse
from kafka import KafkaConsumer
from message_pb2 import Message
from prometheus_client import Counter, generate_latest

__all__ = ['addr_to_location']

logger = logging.getLogger('kafka')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)


def addr_to_location(addr):
    """ :return province, city """
    if ipaddress.ip_address(addr).is_private:
        return "private", "private"
    url = 'http://uc.nxin.com/area/getAreaByIp'
    try:
        resp = requests.post(url, data={"ip": addr})
        data = resp.json()
        if data["code"] != 0:
            logger.info("uc Error: {}, ip {}".format(data, addr))
            return "unkown", "unkown"
        d = data["data"]
        return d["province"], d["city"]
    except Exception:
        # ConnectionError
        logger.info("uc ConnectionError: ip {}".format(addr))
        return "unkown", "unkown"


message = Message()
consumer = KafkaConsumer(
    'nginx-access-log',
    value_deserializer=message.ParseFromString,
    bootstrap_servers=['10.211.12.23:9092',
                       '10.211.12.24:9092',
                       '10.211.12.25:9092'])

c_remote = Counter('ngx_remote_addr_counter', 'remote addr counter',
                   ['instance', 'domain', 'province', 'city'])
c_device = Counter('ngx_user_agent_counter', 'remote addr counter',
                   ['instance', 'domain', 'device', 'os', 'browser'])


class KafkaConsumer(threading.Thread):

    def __init__(self):
        super().__init__()

    def run(self):
        for _ in consumer:
            ngx_hostname = message.hostname
            domain = message.logger
            remote_addr = message.fields[5].value_string[0]
            province, city = addr_to_location(remote_addr)
            try:
                user_agent = message.fields[6].value_string[0]
                ua = parse(user_agent)
                device = ua.device.family
                os = ua.os.family
                browser = ua.browser.family
            except IndexError:
                # user agent is emtpy in ngx log
                device = "null"
                os = "null"
                browser = "null"
            finally:
                c_remote.labels(instance=ngx_hostname, domain=domain, province=province, city=city).inc()
                c_device.labels(instance=ngx_hostname, domain=domain, device=device, os=os, browser=browser).inc()


app = Flask(__name__)


@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain; version=0.0.4; charset=utf-8')


if __name__ == '__main__':
    # Start up the server to expose the metrics.
    kc = KafkaConsumer()
    kc.start()
    app.run(host='0.0.0.0', port=8000)
