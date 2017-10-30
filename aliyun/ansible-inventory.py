import os
import json
import argparse
from time import time
from collections import defaultdict
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest

# https://help.aliyun.com/document_detail/25506.html

access_key = ""
access_key_secret = ""
region_id = 'cn-beijing'
client = AcsClient(access_key, access_key_secret, region_id)


def get_instances():
    page_number = 1
    count = 0
    total_count = 0

    while page_number == 1 or count < total_count:
        req = DescribeInstancesRequest.DescribeInstancesRequest()
        req.add_query_param('PageSize', 100)
        req.add_query_param('PageNumber', page_number)
        body = client.do_action_with_exception(req)
        data = json.loads(body.decode("utf-8"))
        total_count = data['TotalCount']
        instances = data['Instances']['Instance']
        count += len(instances)
        page_number += 1

        for instance in data['Instances']['Instance']:
            yield instance


index = defaultdict(list, {'_meta': {'hostvars': {}}})
cache_file = 'ansible-aliyun.cache'
cache_max_age = 86400


def add_instance(index):
    for instance in get_instances():

        if instance['OSType'] != 'linux':
            continue

        hostname = instance['HostName']
        index[region_id].append(hostname)
        ssh_options = {
            'ansible_ssh_user': "root",
            'ansible_ssh_host': instance['VpcAttributes']['PrivateIpAddress']['IpAddress'][0],
            'ansible_ssh_port': 22,
        }
        index['_meta']['hostvars'][hostname] = dict(ssh_options, aliyun=instance)


def is_cache_valid():
    if os.path.isfile(cache_file):
        mod_time = os.path.getmtime(cache_file)
        current_time = time()
        return (mod_time + cache_max_age) > current_time

    return False


def write_cache():
    add_instance(index)
    data = json.dumps(index, indent=2)
    cache = open(cache_file, 'w')
    cache.write(data)
    cache.close()


def read_cache():
    global index
    cache = open(cache_file, 'r')
    index = json.loads(cache.read())


def refresh():
    if is_cache_valid():
        write_cache()
    else:
        read_cache()


def parse_args():
    parser = argparse.ArgumentParser(description="AliYun Dynamic Inventory")
    parser.add_argument('--refresh', action='store_true',
                        help='Refresh cached information')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true',
                       help='List active servers')
    group.add_argument('--host', help='List details about the specific hostname')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.refresh:
        refresh()
    if args.list:
        refresh()
        print(json.dumps(index, indent=2))
    elif args.host:
        refresh()
        host_vars = index['_meta']['hostvars'][args.host] or {}
        print(json.dumps(host_vars, indent=2))
