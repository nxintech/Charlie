# -*- coding: utf-8 -*-
import sys
import simplejson as json
import logging as log
from kombu import Connection
from kombu import Exchange
from kombu import Queue
from kombu.mixins import ConsumerMixin

# https://wiki.openstack.org/wiki/SystemUsageData#Event_Types_and_Payload_data:
# https://gist.github.com/vagelim/64b355b65378ecba15b0

log.basicConfig(stream=sys.stdout, level=log.DEBUG)

hosts = ("yourip:5672",)
user = "openstack"
password = ""
exchange_name = "nova"
routing_key = "notifications.info"
queue_name = "notifications.info"


def extract(oslo_message):
    data = {"project_id": oslo_message["_context_project_id"]}
    payload = oslo_message["payload"]
    data["hostname"] = payload["hostname"]
    fixed_ip = payload["fixed_ips"][0]
    data["address"] = fixed_ip["address"]
    data["mac"] = fixed_ip["vif_mac"]
    data["instance_id"] = payload["instance_id"]
    image_meta = payload["image_meta"]
    data["os_username"] = image_meta["os_username"]
    data["os_password"] = image_meta["os_password"]
    return data


class NotificationsDump(ConsumerMixin):
    def __init__(self, connection):
        self.connection = connection

    def get_consumers(self, consumer, channel):
        exchange = Exchange(exchange_name, type="topic", durable=True)
        queue = Queue(queue_name, exchange, routing_key=routing_key, durable=True)
        return [consumer(queue, callbacks=[self.on_message])]

    def on_message(self, body, message):
        oslo_message = json.loads(body["oslo.message"])
        if oslo_message["event_type"].startswith("compute.instance.create.end"):
            data = extract(oslo_message)
            log.info("data :%s" % data)
        elif oslo_message["event_type"].startswith("compute.instance.delete.end"):
            log.info('Body: %r' % body)
        message.ack()

url = "amqp://" + ";".join(["{}:{}@{}".format(user, password, host) for host in hosts]) + "/"
with Connection(url, heartbeat=15) as conn:
    NotificationsDump(conn).run()
