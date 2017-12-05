import os
import pickle
import asyncio
import platform
import argparse
import ujson as json
from collections import defaultdict

if platform.platform().startswith('Linux'):
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from zssdk3 import ZStackClient, \
    QueryVmInstanceAction, \
    QuerySystemTagAction, QueryUserTagAction, \
    QueryOneVmInstance


def get_instances(limit=100):
    q = QueryVmInstanceAction()
    q.conditions = ["type=UserVm"]
    q.replyWithCount = True
    q.limit = limit
    q.start = 0
    total = 0
    count = 0

    while q.start == 0 or count < total:
        resp = loop.run_until_complete(client.request_action(q))
        value = resp["value"]
        total = value["total"]
        instances = value["inventories"]

        for instance in instances:
            yield instance

        count += len(instances)
        q.start += q.limit


def query(service=None):
    conditions = ["type=UserVm"]
    if service:
        conditions.append("__userTag__~=app::{}%".format(service))

    q = QueryVmInstanceAction()
    q.conditions = conditions
    q.fields = ["name"]
    return q


def inventory_data():
    result = defaultdict(list)
    result['_meta'] = {'hostvars': {}}
    maps = {}  # {hostname: uuid} maps

    for instance in get_instances():
        hostname = instance["name"]
        maps[hostname] = instance["uuid"]

        if instance["state"] == "Destroyed" \
                or instance["platform"] != "Linux":
            continue

        result['all'].append(hostname)
        result['_meta']['hostvars'][hostname] = {
            'ansible_ssh_user': "root",
            'ansible_ssh_host': instance["vmNics"][0]["ip"],
            'ansible_ssh_port': 22,
            'zstack': instance
        }

    # host aggregate by user tag
    tasks = []
    index = 0
    for tag in get_user_tags():
        if tag.startswith('app::'):
            app, service, version = tag.split("::")
            if service in service_cache:
                continue
            service_cache[service] = index
            q = query(service=service)
            tasks.append(client.request_action(q))
            index += 1

    reverse_cache = {v: k for k, v in service_cache.items()}
    results = loop.run_until_complete(asyncio.gather(*tasks))

    for i, r in enumerate(results):
        for fields in r['value']['inventories']:
            hostname = fields['name']
            service = reverse_cache[i]
            result[service].append(hostname)

    return result, maps


def get_system_tags():
    q = QuerySystemTagAction()
    q.conditions = ["inherent=true", "resourceType=VmInstanceVO"]
    q.fields = ["tag"]

    resp = loop.run_until_complete(client.request_action(q))

    for tag in resp["value"]["inventories"]:
        yield tag["tag"]


def get_user_tags():
    q = QueryUserTagAction()
    q.conditions = ["resourceType=VmInstanceVO"]
    q.fields = ["tag"]

    resp = loop.run_until_complete(client.request_action(q))

    for tag in resp["value"]["inventories"]:
        yield tag["tag"]


def get_host(hostname):
    if not os.path.exists(".cache"):
        d, maps = inventory_data()
        with open(".cache", 'wb') as f:
            pickle.dump(maps, f)

        return d['_meta']['hostvars'][hostname] or {}

    with open(".cache", 'rb') as f:
        unpickler = pickle.Unpickler(f)
        maps = unpickler.load()
        if not isinstance(maps, dict):
            raise ValueError()

    q = QueryOneVmInstance()
    q.uuid = maps[hostname]
    resp = loop.run_until_complete(client.request_action(q))

    instance = resp["value"]["inventories"][0]
    host_vars = {
        'ansible_ssh_user': "root",
        'ansible_ssh_host': instance["vmNics"][0]["ip"],
        'ansible_ssh_port': 22,
        'zstack': instance
    }
    return host_vars


def parse_args():
    parser = argparse.ArgumentParser(description="Zstack Dynamic Inventory")
    # ansible dynamic inventory args
    g = parser.add_mutually_exclusive_group()
    g.add_argument('--list', action='store_true',
                   help='list all servers, conflict with --host')
    g.add_argument('--host',
                   help='list details about the specific hostname')
    parser.add_argument('--app', action='store_true',
                        help='list all ansible host group')

    parser.add_argument('--show', action='store_true',
                        help='show specific ansible host group')

    parser.add_argument('--map', action='store_true',
                        help='show vm hostname uuid map')
    return parser.parse_args()


if __name__ == '__main__':
    # global settings
    loop = asyncio.get_event_loop()
    client = ZStackClient(host="zstack.nxin.com", loop=loop)
    client.set_session("account", "username", "password")
    service_cache = {}
    args = parse_args()
    if args.list:
        data, maps = inventory_data()
        with open(".cache", 'wb') as f:
            pickle.dump(maps, f)
        print(json.dumps(data, indent=2))

    if args.host:
        print(json.dumps(get_host(args.host), indent=2))

    if args.app:
        inventory_data()
        print(service_cache.keys())

    if args.show:
        data, _ = inventory_data()
        print(data[args.show])

    if args.map:
        with open('.cache', 'rb') as f:
            print(json.dumps(pickle.load(f), indent=2))