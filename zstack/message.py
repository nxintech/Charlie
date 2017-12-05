import uuid
import json
import redis
import logging
from functools import partial
from kombu import Connection
from kombu import Exchange
from kombu import Queue
from kombu import binding
from kombu.mixins import ConsumerMixin

from jumpserver import JumpServer

# How this script works
# create_vm_event.success ->
#   1 store vm inventory in redis
#   2 add vm in jump
#
# destroy_vm_event.success -> inactive vm in jump
#
# recover_vm_event.success -> active vm in jump
#
# expunge_vm_event.success ->
#   1 get vm inventory from redis
#   2 delete vm in jump
#   3 if delete ok, delete vm inventory from redis

# set logger
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

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
expunge_vm = 'org.zstack.header.vm.APIExpungeVmInstanceEvent'

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

        # ZStack msg
        if destroy_msg in event:
            body = event[destroy_msg]
            api_id = body['id']
            vm_uuid = body['uuid']
            redis_api_set(api_id, vm_uuid)
            logger.info('destroy_msg: apiId {} vmUuid {}'.format(api_id, vm_uuid))

        elif recover_msg in event:
            body = event[recover_msg]
            api_id = body['id']
            redis_api_set(api_id, '1')
            logger.info('recover_msg: apiId {}'.format(api_id))

        elif expunge_msg in event:
            body = event[expunge_msg]
            api_id = body['id']
            vm_uuid = body['uuid']
            redis_api_set(api_id, vm_uuid)
            logger.info('expunge_msg: apiId {} vmUuid {}'.format(api_id, vm_uuid))

        # Aliyun msg
        elif delete_vm_remote_msg_ali in event:
            body = event[delete_vm_remote_msg_ali]
            api_id = body['headers']['task-context']['api']
            vm_uuid = body['ecsId']
            redis_api_set(api_id, vm_uuid)
            logger.info('aliyun_delete_remote_msg: apiId {} ecsId {}'.format(api_id, vm_uuid))

        message.ack()

    def on_canonical_event(self, body, message):
        # event = json.loads(body)
        #
        # if canonical_event in event:
        #     body = event[canonical_event]
        #     if body['path'] == '/vm/state/change' and body['content']['newState'] == "Destroyed":
        #         inventory = body['content']['inventory']
        #         vm_uuid, hostname, ip = parse(inventory)
        #
        #         # we need cache all Destroyed VM inventory
        #         #  in redis, so when VM is expunged
        #         # wo can get VM inventory from redis
        #         redis_vm_set(vm_uuid, json.dumps(inventory))
        #         logger.info(
        #             'canonical_destroyed: redis hset vmUuid {}, hostname {}, ip {}, state Destroyed'
        #             .format(vm_uuid, hostname, ip))

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
                inventory = body["inventory"]
                vm_uuid, hostname, ip = parse(inventory)

                if inventory['type'] != 'UserVm' or inventory['platform'] != 'Linux':
                    logger.info("create_vm: VM type is not 'UserVm', or platform is not 'Linux',"
                                " vmUuid {} hostname {} ip {}".format(vm_uuid, hostname, ip))
                    return message.ack()

                redis_vm_set(vm_uuid, json.dumps(inventory))
                logger.info('create_vm: redis hset vmUuid {} hostname {} ip {}'.format(vm_uuid, hostname, ip))

                code = js.add_resource(hostname, 'root', "no_need", ip=ip)
                logger.info("create_vm: jump add vmUuid {} hostname {} ip {},"
                            " status code {}".format(vm_uuid, hostname, ip, code))

        elif create_vm_ali in event:
            body = event[create_vm_ali]
            if body["success"]:
                inventory = body['inventory']

                # TODO aliyun check VM os Type

                vm_uuid, hostname, ip = parse_ali(inventory)
                redis_vm_set(vm_uuid, json.dumps(inventory))
                logger.info('aliyun_create_vm: redis hset vmUuid {} hostname {} ip {}'.format(vm_uuid, hostname, ip))

                code = js.add_resource(hostname, 'root', inventory['ecsInstanceRootPassword'], ip=ip)
                logger.info("aliyun_create_vm: jump add vmUuid {} hostname {} ip {},"
                            " status code {}".format(vm_uuid, hostname, ip, code))

        elif destroy_vm in event:
            body = event[destroy_vm]
            api_id = body['apiId']

            vm_uuid = redis_api_get(api_id)
            if vm_uuid is not None and body["success"]:
                inventory = redis_vm_get(vm_uuid)
                if inventory is None:
                    logger.info('destroy_vm: vmUuid {} not in redis'.format(vm_uuid))
                    return message.ack()

                _, hostname, ip = parse(json.loads(inventory.decode('utf-8')))

                asset_id, asset = js.search_resource(hostname)
                if asset_id is None:
                    logger.info(
                        'destroy_vm: vmUuid {} hostname {} ip {} '
                        'not found in jumpserver'.format(vm_uuid, hostname, ip))
                    return message.ack()

                asset['is_active'] = '0'
                code = js.edit_resource(asset_id, asset)
                logger.info('destroy_vm: jump inactive vmUuid {} hostname {} ip {},'
                            ' status code {}'.format(vm_uuid, hostname, ip, code))

            # no matter event successful
            # we del this api_id in redis
            redis_api_del(api_id)

        elif recover_vm in event:
            body = event[recover_vm]
            api_id = body['apiId']

            if redis_api_get(api_id) is not None and body["success"]:
                # inventory is just in event
                # dont need get from redis
                inventory = body["inventory"]
                vm_uuid, hostname, ip = parse(inventory)
                asset_id, asset = js.search_resource(hostname)
                if asset_id is None:
                    logger.info(
                        'recover_vm: uuid {} hostname {} ip {},'
                        ' not found in jumpserver'.format(vm_uuid, hostname, ip))
                    return message.ack()

                asset['is_active'] = '1'
                code = js.edit_resource(asset_id, asset)
                logger.info('recover_vm: jump active vmUuid {} hostname {} ip {},'
                            ' status code {}'.format(vm_uuid, hostname, ip, code))

            redis_api_del(api_id)

        elif expunge_vm in event:
            body = event[expunge_vm]
            api_id = body['apiId']

            vm_uuid = redis_api_get(api_id)
            if vm_uuid is not None and body["success"]:
                inventory = redis_vm_get(vm_uuid)
                if inventory is None:
                    logger.info('expunge_vm: vmUuid {} not in redis'.format(vm_uuid))
                    return message.ack()

                _, hostname, ip = parse(json.loads(inventory.decode('utf-8')))

                asset_id, asset = js.search_resource(hostname)
                if asset_id is None:
                    logger.info('expunge_vm: vmUuid {} hostname {} ip {}'
                                ' not found in jumpserver'.format(vm_uuid, hostname, ip))
                    return message.ack()

                code = js.del_resource(asset_id)
                logger.info('expunge_vm: jump delete vmUuid {} hostname {} ip {},'
                            ' status code {}'.format(vm_uuid, hostname, ip, code))

                if code == 200:
                    redis_vm_del(vm_uuid)
                    logger.info('expunge_vm: redis hdel vmUuid {} hostname {} ip {}'
                                .format(vm_uuid, hostname, ip))

            redis_api_del(api_id)

        elif delete_vm_ali in event:
            body = event[delete_vm_ali]
            api_id = body['headers']['task-context']['api']

            vm_uuid = redis_api_get(api_id)
            if vm_uuid is not None and body["success"]:
                inventory = redis_vm_get(vm_uuid)
                if inventory is None:
                    logger.info('aliyun_delete_vm: vmUuid {} not in redis'.format(vm_uuid))
                    return message.ack()

                _, hostname, ip = parse_ali(json.loads(inventory.decode('utf-8')))

                asset_id, _ = js.search_resource(hostname)
                if asset_id is None:
                    logger.info('aliyun_delete_vm: vmUuid {} hostname {} ip {}'
                                ' not found in jumpserver'.format(vm_uuid, hostname, ip))
                    return message.ack()

                code = js.del_resource(asset_id)
                logger.info('aliyun_delete_vm: jump delete vmUuid {} hostname {} ip {},'
                            ' status code {}'.format(vm_uuid, hostname, ip, code))

                if code == 200:
                    redis_vm_del(vm_uuid)
                    logger.info('aliyun_delete_vm: redis hdel vmUuid {} hostname {} ip {}'
                                .format(vm_uuid, hostname, ip))

            redis_api_del(api_id)

        message.ack()


def parse(inventory):
    vm_uuid = inventory["uuid"]
    hostname = inventory["name"]
    # vm must assign static ip
    # do not use DHCP
    ip = inventory["vmNics"][0].get("ip", '')
    return vm_uuid, hostname, ip


def parse_ali(inventory):
    vm_uuid = inventory['ecsInstanceId']
    hostname = inventory["name"]
    ip = inventory.get('privateIpAddress', '')
    return vm_uuid, hostname, ip


if __name__ == '__main__':
    url = "amqp://user:password@zstack_manager:5672"
    js = JumpServer("user", "password", base="http://jump.t.nxin.com/")
    pool = redis.ConnectionPool(host='192.168.0.1', port=6379, db=0)
    db = redis.Redis(connection_pool=pool)
    # pass redis hash name to partial fuction
    redis_api_set = partial(db.hset, 'ZSTACK_API_ID')
    redis_api_get = partial(db.hget, 'ZSTACK_API_ID')
    redis_api_del = partial(db.hdel, 'ZSTACK_API_ID')
    redis_vm_set = partial(db.hset, 'ZSTACK_VM_INVENTORY')
    redis_vm_get = partial(db.hget, 'ZSTACK_VM_INVENTORY')
    redis_vm_del = partial(db.hdel, 'ZSTACK_VM_INVENTORY')

    with Connection(url, heartbeat=15) as conn:
        ZStackConsumer(conn).run()
