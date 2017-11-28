# -*- coding:utf-8 -*-
import requests


class JumpServer(object):
    def __init__(self, username, password, base="http://127.0.0.1/"):
        self._cookie = None
        self.username = username
        self.password = password
        self.base = base

    def get_cookie(self):
        if not self._cookie:
            url = self.base + "login/"
            data = {
                "username": self.username,
                "password": self.password
            }
            res = requests.post(url=url, data=data)
            self._cookie = res.cookies
        return self._cookie

    def add_resource(self, hostname, username, password,
                     port, ip=None, group=None, is_active=1):
        url = self.base + "jasset/asset/add/"
        data = {
            "hostname": hostname,
            "ip": ip,
            "username": username,
            "password": password,
            "port": port,
            "group": group,
            "is_active": is_active
        }
        res = requests.post(url=url, data=data, cookies=self.get_cookie())
        return res.status_code

    def del_resource(self, resource_id):
        url = self.base + "jasset/asset/del/?id={}".format(resource_id)
        res = requests.get(url=url, cookies=self.get_cookie())
        return res.status_code

    def search_resource(self, hostname):
        url = self.base + "jasset/asset/search/?hostname={}".format(hostname)
        res = requests.get(url=url, cookies=self.get_cookie())
        data = res.json()[0]
        resource_id = data['pk']
        resource_data = data['fields']
        return resource_id, resource_data

    def edit_resource(self, resource_id, data):
        url = self.base + "jasset/asset/edit/?id={}".format(resource_id)
        res = requests.post(url=url, data=data, cookies=self.get_cookie())
        return res.status_code


if __name__ == "__main__":
    js = JumpServer("your username", "your passowrd", base="http://jump.t.nxin.com")
    print(js.add_resource("host1", "root", "root123", 22))
