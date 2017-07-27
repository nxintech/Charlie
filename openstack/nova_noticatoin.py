# -*- coding: utf-8 -*-

# https://wiki.openstack.org/wiki/SystemUsageData#Event_Types_and_Payload_data:
# https://gist.github.com/vagelim/64b355b65378ecba15b0


import logging
import simplejson as json
from kombu import Connection
from kombu import Exchange
from kombu import Queue
from kombu.mixins import ConsumerMixin

from metad import Client

# set logger
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
log = logging.getLogger()

# set rabbit
hosts = ("yourip:5672",)
user = "openstack"
password = ""
exchange_name = "nova"
routing_key = "notifications.info"
queue_name = "notifications.info"

# metad clinet
client = Client()


class NotificationsDump(ConsumerMixin):
    def __init__(self, connection):
        self.connection = connection

    def get_consumers(self, consumer, channel):
        exchange = Exchange(exchange_name, type="topic", durable=True)
        queue = Queue(queue_name, exchange, routing_key=routing_key, durable=True)
        return [consumer(queue, callbacks=[self.on_message])]

    def on_message(self, body, message):
        oslo_message = json.loads(body["oslo.message"])
        event_type = oslo_message["event_type"]

        if event_type == "compute.instance.create.end":
            data = extract(oslo_message)
            instance_id = data["instance_id"]
            log.info("instance create :%s" % data)

            # add metad data
            endpiont = "/nodes/{}".format(instance_id)
            res = client.mput("data{}".format(endpiont), data)
            log.info("metad put instance :%s, result: %s" % (instance_id, res))

            # add metad mapping
            mapping = {data["hostname"]: {"node": endpiont}}
            res = client.mput("mapping", mapping)
            log.info("metad put mapping :%s, result: %s" % (mapping, res))

        elif event_type == "compute.instance.delete.end":
            data = extract(oslo_message)
            instance_id = data["instance_id"]
            log.info('instance delete : %s' % instance_id)

            # delete metad data
            endpiont = "/nodes/{}".format(instance_id)
            res = client.mdelete("data{}".format(endpiont))
            log.info('metad data delete: %s, result: %s' % (instance_id, res))

            # delete metad mapping
            res = client.mdelete("mapping/{}".format(data["hostname"]))
            log.info('metad mapping delete: %s, result: %s' % (instance_id, res))

        # if not ack, will re-receive message
        message.ack()


def extract(oslo_message):
    data = {"project_id": oslo_message["_context_project_id"]}
    payload = oslo_message["payload"]
    data["hostname"] = payload["hostname"]
    data["instance_id"] = payload["instance_id"]
    image_meta = json.loads(payload["image_meta"]["image_meta"])
    data["os_username"] = image_meta["os_username"]
    data["os_password"] = image_meta["os_password"]

    fixed_ip = payload.get("fixed_ips", None)
    if fixed_ip:
        fixed_ip = fixed_ip[0]
        data["address"] = fixed_ip["address"]
        data["mac"] = fixed_ip["vif_mac"]
    return data

if __name__ == '__main__':
    url = "amqp://" + ";".join(["{}:{}@{}".format(user, password, host) for host in hosts]) + "/"
    with Connection(url, heartbeat=15) as conn:
        NotificationsDump(conn).run()
