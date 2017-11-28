import uuid
import json
import redis
from kombu import Connection
from kombu import Exchange
from kombu import Queue
from kombu import binding
from kombu.mixins import ConsumerMixin

from jumpserver import JumpServer

# redis hash name
api_id_name = 'ZSTACK_API_ID'
vm_inventory_name = 'ZSTACK_VM_INVENTORY'

# event key
canonical_event = "org.zstack.core.cloudbus.CanonicalEvent"

start_vm = 'org.zstack.header.vm.APIStartVmInstanceEvent'
stop_vm = 'org.zstack.header.vm.APIStopVmInstanceEvent'

create_vm = 'org.zstack.header.vm.APICreateVmInstanceEvent'
create_vm_ali = 'org.zstack.header.aliyun.ecs.APICreateEcsInstanceFromEcsImageEvent'

recover_msg = 'org.zstack.header.vm.APIRecoverVmInstanceMsg'
recover_vm = 'org.zstack.header.vm.APIRecoverVmInstanceEvent'

destroy_msg = 'org.zstack.header.vm.APIDestroyVmInstanceMsg'
destroy_vm = 'org.zstack.header.vm.APIDestroyVmInstanceEvent'

expunge_msg = 'org.zstack.header.vm.APIExpungeVmInstanceMsg'
expunge_event = 'org.zstack.header.vm.APIExpungeVmInstanceEvent'

# only delete in ZStack dashboard
delete_vm_msg_ali = 'org.zstack.header.aliyun.ecs.APIDeleteEcsInstanceMsg'

# remoteMsg is make sure vm be deleteed in aliyun
delete_vm_remote_msg_ali = 'org.zstack.header.aliyun.ecs.DeleteEcsInstanceRemoteMsg'
delete_vm_ali = 'org.zstack.header.aliyun.ecs.APIDeleteEcsInstanceEvent'


def uuid4():
    return str(uuid.uuid4()).replace('-', '')


class ZStackConsumer(ConsumerMixin):
    def __init__(self, connection):
        self.connection = connection

        self.uuid = uuid4()
        self.broadcast_exchange = Exchange('BROADCAST', type='topic', passive=True)
        self.p2p_exchange = Exchange('P2P', type='topic', passive=True)

    def get_consumers(self, consumer, channel):
        api_event_queue = Queue(
            "zstack.ui.api.event.%s" % self.uuid,
            exchange=self.broadcast_exchange,
            routing_key="key.event.API.API_EVENT",
            auto_delete=True)

        canonical_event_queue = Queue(
            "zstack.ui.canonical.event.%s" % self.uuid,
            exchange=self.broadcast_exchange,
            routing_key="key.event.LOCAL.canonicalEvent",
            auto_delete=True)

        # self.new_channel = channel.connection.channel()
        reply_queue_name = "zstack.ui.message.%s" % self.uuid
        reply_queue = Queue(
            reply_queue_name,
            # exchange=self.p2p_exchange,
            # routing_key="zstack.message.cloudbus.#",
            [binding(self.p2p_exchange, "zstack.message.vmInstance.#"),
             binding(self.p2p_exchange, "zstack.message.ecs.vm.#"),
             binding(self.p2p_exchange, "zstack.message.aliyun.sdk.#")
             ],
            auto_delete=True)

        return [
            consumer(
                queues=[canonical_event_queue],
                callbacks=[self.on_canonical_event]),
            consumer(
                queues=[api_event_queue],
                callbacks=[self.on_api_event]),
            consumer(
                queues=[reply_queue],
                callbacks=[self.on_message])
        ]

    def on_message(self, body, message):
        event = json.loads(body)

        if destroy_msg in event:
            body = event[destroy_msg]
            api_id = body['id']
            vm_uuid = body['uuid']
            db.hset(api_id_name, api_id, vm_uuid)

        elif recover_vm in event:
            body = event[expunge_msg]
            api_id = body['id']
            db.hset(api_id_name, api_id, '1')

        elif expunge_msg in event:
            body = event[expunge_msg]
            api_id = body['id']
            vm_uuid = body['uuid']
            db.hset(api_id_name, api_id, vm_uuid)

        # aliyun
        elif delete_vm_remote_msg_ali in event:
            body = event[delete_vm_remote_msg_ali]
            api_id = body['headers']['task-context']['api']
            vm_uuid = body['ecsId']
            db.hset(api_id_name, api_id, vm_uuid)

        message.ack()

    def on_canonical_event(self, body, message):
        event = json.loads(body)

        if canonical_event in event:
            body = event[canonical_event]
            if body['path'] == '/vm/state/change':
                content = body['content']
                if content['newState'] == "Destroyed":
                    inventory = content['inventory']
                    task_context = body['headers']['task-context']
                    api_id = task_context['api']

                    vm_uuid = db.hget(api_id_name, api_id)
                    if vm_uuid is not None:
                        # we need cache all VM inventory
                        # which Destroyed
                        db.hset(vm_inventory_name, vm_uuid, json.dumps(inventory))

        message.ack()

    def on_api_event(self, body, message):
        event = json.loads(body)

        if start_vm in event:
            pass

        elif stop_vm in event:
            pass

        elif create_vm in event:
            body = event[create_vm]
            if body["success"]:
                hostname, ip = parse(body["inventory"])
                js.add_resource(hostname, 'root', ip=ip, password="no_need")

        elif create_vm_ali in event:
            body = event[create_vm_ali]
            if body["success"]:
                inventory = body['inventory']
                vm_uuid = inventory['ecsInstanceId']
                db.hset(vm_inventory_name, vm_uuid, json.dumps(inventory))

                hostname = inventory['name']
                ip = inventory['privateIpAddress']
                password = inventory['ecsInstanceRootPassword']
                js.add_resource(hostname, 'root', ip=ip, password=password)

        elif destroy_vm in event:
            body = event[destroy_vm]
            api_id = body['apiId']

            vm_uuid = db.hget(api_id_name, api_id)
            if vm_uuid is not None:
                if body["success"]:
                    inventory = db.hget(vm_inventory_name, vm_uuid)
                    hostname, _ = parse(json.loads(inventory.decode('utf-8')))

                    asset_id, asset = js.search_resource(hostname)
                    # zstack inventory not in jumpserver
                    # just ignore this message
                    if asset_id is None and asset is None:
                        return message.ack()

                    asset['is_active'] = '0'
                    js.edit_resource(asset_id, asset)
                # no matter successful we need del this api id
                db.hdel(api_id_name, api_id)

        elif recover_vm in event:
            body = event[recover_vm]
            api_id = body['apiId']

            res = db.hget(api_id_name, api_id)
            if res is not None:
                if body["success"]:
                    # inventory is just in body
                    # no need get from redis
                    hostname, _ = parse(body["inventory"])
                    asset_id, asset = js.search_resource(hostname)
                    if asset_id is None and asset is None:
                        return message.ack()

                    asset['is_active'] = '1'
                    js.edit_resource(asset_id, asset)

                db.hdel(api_id_name, api_id)

        elif expunge_event in event:
            body = event[expunge_event]
            api_id = body['apiId']

            vm_uuid = db.hget(api_id_name, api_id)
            if vm_uuid is not None:
                if body["success"]:
                    inventory = db.hget(vm_inventory_name, vm_uuid)
                    if inventory is None:
                        return message.ack()

                    hostname, ip = parse(json.loads(inventory.decode('utf-8')))
                    asset_id, _ = js.search_resource(hostname)
                    res = js.del_resource(asset_id)
                    # if res == 200:
                    #     r.hdel(vm_inventory_name, vm_uuid)

                db.hdel(api_id_name, api_id)

        elif delete_vm_ali in event:
            body = event[delete_vm_ali]
            api_id = body['headers']['task-context']['api']
            vm_uuid = db.hget(api_id_name, api_id)
            if vm_uuid is not None:
                if body["success"]:
                    inventory = db.hget(vm_inventory_name, vm_uuid)
                    if inventory is None:
                        return message.ack()

                    hostname, ip = parse_ali(json.loads(inventory.decode('utf-8')))
                    asset_id, _ = js.search_resource(hostname)
                    res = js.del_resource(asset_id)
                    # if res == 200:
                    #     r.hdel(vm_inventory_name, vm_uuid)

                db.hdel(api_id_name, api_id)

        message.ack()


def parse(inventory):
    hostname = inventory["name"]
    # vm must assign static ip
    # do not use DHCP
    ip = inventory["vmNics"][0].get("ip", '')
    return hostname, ip


def parse_ali(inventory):
    hostname = inventory["name"]
    ip = inventory['privateIpAddress']
    return hostname, ip


if __name__ == '__main__':
    url = "amqp://user:password@zstack_manager:5672"
    js = JumpServer("user", "password", base="http://jump.t.nxin.com/")
    db = redis.Redis(host='192.168.0.1', port=6379, db=0)

    with Connection(url, heartbeat=15) as conn:
        ZStackConsumer(conn).run()
