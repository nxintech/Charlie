import os
import re
import six
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

cache_file = 'inventory.cache'
cache_max_age = 86400


def parse_instance():
    data = defaultdict(list)
    data['_meta'] = {'hostvars': {}}
    for instance in get_instances():
        hostname = instance['HostName']
        data[region_id].append(hostname)
        data['_meta']['hostvars'][hostname] = {
            'ansible_ssh_user': "root",
            'ansible_ssh_host': instance['VpcAttributes']['PrivateIpAddress']['IpAddress'][0],
            'ansible_ssh_port': 22,
            'aliyun': instance
        }
    return data


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


def write_cache():
    data = parse_instance()
    with open(cache_file, 'w') as cache:
        cache.write(json.dumps(data, indent=2))
    return data


def read_cache():
    with open(cache_file) as cache:
        return json.loads(cache.read())


def refresh():
    if is_cache_valid():
        return write_cache()
    return read_cache()


def is_cache_valid():
    if os.path.isfile(cache_file):
        mod_time = os.path.getmtime(cache_file)
        current_time = time()
        return (mod_time + cache_max_age) > current_time


def cache_filter(expression, tag):
    cache = refresh()
    if expression:
        return expression_filter(cache, expression)
    if tag:
        return tag_filter(cache, tag)

    return cache


def expression_filter(cache, expression):
    result = defaultdict(list)
    result['_meta'] = {'hostvars': {}}
    attr, regex = expression
    patten = re.compile(regex)

    for hostname, host in cache['_meta']['hostvars'].items():
        if attr == "PrivateIpAddress" and patten.match(host["ansible_ssh_host"]):
            result[region_id].append(hostname)
            result['_meta']['hostvars'][hostname] = host
            continue

        if attr in host["aliyun"] and patten.match(host["aliyun"][attr]):
            result[region_id].append(hostname)
            result['_meta']['hostvars'][hostname] = host

    return result


def tag_filter(cache, tag):
    result = defaultdict(list)
    result['_meta'] = {'hostvars': {}}

    key, value = tag
    for hostname, host in cache['_meta']['hostvars'].items():
        if "Tags" not in host["aliyun"]:
            continue

        for tagkv in host["aliyun"]["Tags"]["Tag"]:
            tagk, tagv = tagkv["TagKey"], tagkv["TagValue"]
            if key == tagk and value == tagv:
                result["%s=%s" % (key, value)].append(hostname)
                result['_meta']['hostvars'][hostname] = host
                break

    return result


class KvAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not namespace.list:
            raise argparse.ArgumentError(namespace.method, "-t only used with argument --list")

        if '=' not in values:
            raise ValueError('Expression allowed format: attribute=regex')

        k, v = values.split('=')
        if option_string == "-e":
            namespace.expression = k, v
        if option_string == "--tag":
            namespace.tag = k, v


def parse_args():
    parser = argparse.ArgumentParser(description="AliYun Dynamic Inventory")
    parser.add_argument('--refresh', action='store_true',
                        help='refresh cached information')

    g = parser.add_mutually_exclusive_group(required=True)

    # ansible dynamic inventory args
    g.add_argument('--list', action='store_true',
                   help='list all servers, conflict with --host')
    g.add_argument('--host', dest="hostname",
                   help='list details about the specific hostname')

    # filter host
    g = parser.add_mutually_exclusive_group()
    g.add_argument('-e', dest="expression", action=KvAction,
                   help="filter expression, format: attribute=regex, "
                        "attribute is Aliyun ECS InstanceAttributesType, see "
                        "https://help.aliyun.com/document_detail/25656.html"
                        "?spm=5176.doc25506.2.4.WXJEtJ for more info")
    g.add_argument('--tag', action=KvAction, type=string,
                   help="tag expression, format: TagKey=TagValue, "
                        "tag pair is Aliyun ECS InstanceAttributesType Tags")

    return parser.parse_args()


def string(s):
    if six.PY3:
        return s
    else:
        return unicode(s, 'utf8')


if __name__ == '__main__':
    args = parse_args()
    if args.refresh:
        refresh()
    if args.list:
        data = cache_filter(args.expression, args.tag)
        print(json.dumps(data, indent=2))
    elif args.host:
        data = refresh()
        host_vars = data['_meta']['hostvars'][args.host] or {}
        print(json.dumps(host_vars, indent=2))
