#!/usr/bin/env python
import os
import re
import six
import json
import time
import tempfile
import argparse
import subprocess
from collections import defaultdict
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest


# https://help.aliyun.com/document_detail/25506.html
# https://github.com/yekeqiang/post/blob/master/original/Ansible%20--%20%E5%BC%80%E5%8F%91%E5%8A%A8%E6%80%81%E7%9A%84%20Inventory%20%E6%BA%90.markdown


access_key = ""
access_key_secret = ""
region_id = "cn-beijing"
client = AcsClient(access_key, access_key_secret, region_id)


def inventory_data():
    result = defaultdict(list)
    no_tag = result["notag"]
    result['_meta'] = {'hostvars': {}}
    for instance in get_instances():
        hostname = instance['HostName']

        # host aggregate by tag
        if "Tags" not in instance:
            no_tag.append(hostname)
        else:
            for kv_pairs in instance["Tags"]["Tag"]:
                result[kv_pairs["TagValue"]].append(hostname)

        result['_meta']['hostvars'][hostname] = {
            'ansible_ssh_user': "root",
            'ansible_ssh_host': instance['VpcAttributes']['PrivateIpAddress']['IpAddress'][0],
            'ansible_ssh_port': 22,
            'aliyun': instance
        }
    return result


def get_instances():
    page_number = 1
    count = 0
    total_count = 0

    while page_number == 1 or count < total_count:
        data = request(page_number)
        total_count = data['TotalCount']
        instances = data['Instances']['Instance']

        for instance in instances:
            yield instance

        count += len(instances)
        page_number += 1


def request(page):
    req = DescribeInstancesRequest.DescribeInstancesRequest()
    req.add_query_param('PageSize', 100)
    req.add_query_param('PageNumber', page)
    body = client.do_action_with_exception(req)
    return json.loads(body.decode("utf-8"))


class Cache(object):
    def __init__(self):
        self.file = ".cache"
        self.max_age = 86400  # 24h

    def is_valid(self):
        mtime = os.path.getmtime(self.file)
        now = time.time()
        return (mtime + self.max_age) > now

    def read(self, lines=False):
        with open(self.file) as f:
            if lines:
                return f.readlines()
            return f.read()

    def write(self, data):
        with open(self.file, "w") as f:
            f.write(data)


cache = Cache()


def refresh():
    data = inventory_data()
    # add '\n' new line for ignore git warning:
    # '\ No newline at end of file'
    cache.write(json.dumps(data, indent=2) + '\n')
    return data


def get_data():
    if is_cache_valid():
        return json.loads(cache.read())

    return refresh()


def is_cache_valid():
    if os.path.isfile(cache.file):
        mod_time = os.path.getmtime(cache.file)
        now = time.time()
        return (mod_time + cache.max_age) > now


def data_filter(data, expression, tag):
    if expression:
        return exp_filter(data, expression)
    if tag:
        return tag_filter(data, tag)

    return data


def exp_filter(data, expression):
    result = []
    attr, regex = expression
    patten = re.compile(regex)

    for hostname, host in data['_meta']['hostvars'].items():
        if attr == "PrivateIpAddress" and patten.match(host["ansible_ssh_host"]):
            result.append(hostname)
            continue

        if attr in host["aliyun"] and patten.match(host["aliyun"][attr]):
            result.append(hostname)

    return result


def tag_filter(data, tag):
    result = []

    key, value = tag
    for hostname, host in data['_meta']['hostvars'].items():
        if "Tags" not in host["aliyun"]:
            continue

        for kv in host["aliyun"]["Tags"]["Tag"]:
            k, v = kv["TagKey"], kv["TagValue"]
            if key == k and value == v:
                result.append(hostname)
                break

    return result


def temp_write(data):
    temp = tempfile.NamedTemporaryFile()
    temp.write(data)
    temp.seek(0)
    return temp


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

    g = parser.add_mutually_exclusive_group()

    # ansible dynamic inventory args
    g.add_argument('--list', action='store_true',
                   help='list all servers, conflict with --host')
    g.add_argument('--host',
                   help='list details about the specific hostname')

    # host filter argument
    g = parser.add_mutually_exclusive_group()
    g.add_argument('-e', dest="expression", action=KvAction,
                   help="filter expression, format: attribute=regex, "
                        "attribute is Aliyun ECS InstanceAttributesType, see "
                        "https://help.aliyun.com/document_detail/25656.html"
                        "?spm=5176.doc25506.2.4.WXJEtJ for more info")
    g.add_argument('--tag', action=KvAction, type=lambda s: s if six.PY3 else unicode(s, 'utf8'),
                   help="tag expression, format: TagKey=TagValue, "
                        "tag pair is Aliyun ECS InstanceAttributesType Tags")

    return parser.parse_args()


if __name__ == '__main__':
    if not os.path.exists(cache.file):
        refresh()

    args = parse_args()
    if args.refresh:
        # refresh and show diff
        old = temp_write(cache.read() + '\n')
        new = temp_write(json.dumps(refresh(), indent=2) + '\n')
        cmd = "git diff %s %s" % (old.name, new.name)
        subprocess.call(cmd, shell=True)
        old.close()
        new.close()

    if args.list:
        data = data_filter(get_data(), args.expression, args.tag)
        print(json.dumps(data, indent=2))

    if args.host:
        data = get_data()
        host_vars = data['_meta']['hostvars'][args.host] or {}
        print(json.dumps(host_vars, indent=2))
