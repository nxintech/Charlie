#!/usr/local/bin/python
# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import sys
import json
import argparse
import requests

"""
  有云api获取主机名称列表
  输出主机列表格式为 ansible dynamic inventory 格式

  有云api doc
    https://docs.ustack.com/api_doc/index.html

  ansible dynamic inventory doc
    http://docs.ansible.com/ansible/intro_dynamic_inventory.html
"""

# Identity 有云 token 管理域名
Identity = "http://identity.yourdomain.com"
# Compute 有云主机管理域名
Compute = "http://compute.api.yourdomain.com"

INTERNAL_NET_PREFIX = ["192.", "172.", "10."]  # 内网ip前缀


class UOS(object):
    def __init__(self, user_id, password, project_id):
        self.user_id = user_id
        self.password = password
        self.project_id = project_id

    @property
    def token(self):
        return self._get_token()

    def _get_token(self):
        url = "{}/v3/auth/tokens".format(Identity)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        body = {
            "auth": {
                "scope": {
                    "project": {"id": self.project_id}
                },
                "identity": {
                    "password": {
                        "user": {
                            "password": self.password,
                            "id": self.user_id
                        }
                    },
                    "methods": ["password"]
                }
            }
        }
        req = requests.post(url, json=body, headers=headers)
        return req.headers["X-Subject-Token"]

    def get_all_servers_basic_info(self):
        url = "{}/v2/{}/servers".format(Compute, self.project_id)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': self.token
        }
        req = requests.get(url, headers=headers)
        return json.loads(req.text)


def parse_args():
    """ 解析命令行参数 """
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true')
    group.add_argument('--host')
    return parser.parse_args()


def data_parse_by_hostname(data):
    ret = {}
    hostnames = []
    for server in data["servers"]:
        addresses = server["addresses"]
        area_name = addresses.keys()[0]  # found that only have one area_name so far
        if area_name not in ret:
            ret[area_name] = {"hosts": []}
        hostname = server["name"]
        ret[area_name]["hosts"].append(hostname)
        hostnames.append(hostname)
    return ret, hostnames


def data_parse(data):
    """ 过滤 UStack api 返回的数据，提取 ansible 使用的信息 """
    ret = {}
    ip_list = []
    for server in data["servers"]:
        addresses = server["addresses"]
        area_name = addresses.keys()[0]  # found that only have one area_name so far
        if area_name not in ret:
            ret[area_name] = {"hosts": []}
        for block in addresses[area_name]:
            ip = block["addr"]
            if any(map(ip.startswith, INTERNAL_NET_PREFIX)):
                ret[area_name]["hosts"].append(ip)
                ip_list.append(ip)
    return ret, ip_list


def main(user_id, password, project_id):
    args = parse_args()
    uos = UOS(user_id, password, project_id)
    raw_data = uos.get_all_servers_basic_info()
    data, ip_list = data_parse(raw_data)
    data, hostnames = data_parse_by_hostname(raw_data)
    if args.list:
        json.dump(data, sys.stdout)
    if args.host:
        ansible_format = {
            "ansible_ssh_host": args.host,
            "ansible_ssh_port": 22,
            "ansible_ssh_user": "root"
        } if args.host in ip_list or args.host in hostnames else None
        json.dump(ansible_format, sys.stdout)


if __name__ == '__main__':
    user_id = ""
    password = ""
    project_id = ""
    main(user_id, password, project_id)