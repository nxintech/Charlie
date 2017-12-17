#!/usr/bin/env python
import os
import inspect
import asyncio
import platform
import argparse

try:
    import ujson as json
except ModuleNotFoundError:
    import json
from collections import defaultdict

if platform.platform().startswith('Linux'):
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from zssdk3 import ZStackClient, \
    QueryVmInstanceAction, QueryOneVmInstance, \
    QuerySystemTagAction, QueryUserTagAction

basedir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
cache_file = os.path.join(basedir, '.cache')
maps_file = os.path.join(basedir, '.map')


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


def query_app(service=None):
    # query vm that user tag start with app
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
    service_cache = {}
    index = 0
    for tag in get_user_tags():
        if tag.startswith('app::'):
            app, service, version = tag.split("::")
            if service in service_cache:
                continue
            service_cache[service] = index
            q = query_app(service=service)
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
    if not os.path.exists(cache_file):
        data, maps = refresh()
        return data['_meta']['hostvars'][hostname] or {}

    with open(maps_file) as f:
        maps = json.loads(f.read())

    if hostname not in maps:
        return {}

    # hostname not in vm hostname uuid map
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


def read_cache():
    with open(cache_file) as f:
        return json.loads(f.read())


def refresh():
    data, maps = inventory_data()
    with open(maps_file, 'w') as f:
        f.write(json.dumps(maps, indent=2))
    with open(cache_file, 'w') as f:
        f.write(json.dumps(data))
    return data, maps


def parse_args():
    parser = argparse.ArgumentParser(description="Zstack Dynamic Inventory")

    # list and host is exclusive
    g = parser.add_mutually_exclusive_group()
    g.add_argument('--list', action='store_true',
                   help='list all servers, conflict with --host')
    g.add_argument('--host',
                   help='show details of the specific hostname')

    parser.add_argument('--groups', action='store_true',
                        help='list all ansible host group')

    parser.add_argument('--group',
                        help='show hostnames of specific host group')

    parser.add_argument('--map', action='store_true',
                        help='show vm hostname uuid map')

    parser.add_argument('--refresh', action='store_true',
                        help='refresh hostname uuid map and host group cache')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.list:
        data, _ = refresh()
        print(json.dumps(data, indent=2))

    if args.host:
        print(json.dumps(get_host(args.host), indent=2))

    if args.groups:
        data = read_cache()
        # for bash completion
        print(" ".join(data.keys()))

    if args.group:
        data = read_cache()
        print(data[args.group])

    if args.map:
        with open(maps_file) as f:
            print(f.read())

    if args.refresh:
        refresh()


if __name__ == '__main__':
    # global settings
    loop = asyncio.get_event_loop()
    client = ZStackClient(host="zstack.nxin.com", loop=loop)
    client.set_session("account", "username", "password")
    main()
    loop.run_until_complete(client.close())
