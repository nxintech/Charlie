# -*- coding:utf-8 -*-
import requests
from urllib.parse import urlparse


class JumpServer(object):
    def __init__(self, username, password, base="http://127.0.0.1/"):
        self._cookie = None
        self.username = username
        self.password = password
        self.base = base
        self.get_cookie()

    @property
    def cookie(self):
        if self._cookie is None:
            self._cookie = self.get_cookie()
            return self._cookie

        def is_expired():
            domain = urlparse(self.base).netloc
            for cookie in self._cookie:
                if cookie.name == domain:
                    return cookie.is_expired()

        if is_expired():
            self._cookie = self.get_cookie()
            return self._cookie

        return self._cookie

    def get_cookie(self):
        url = self.base + "login/"
        data = {
            "username": self.username,
            "password": self.password
        }
        res = requests.post(url=url, data=data)
        return res.cookies

    def add_resource(self, hostname, username, password,
                     port=22, ip=None, group=1, is_active=1):
        # asset group 1 include vm, default group
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
        res = requests.post(url=url, data=data, cookies=self.cookie)
        return res.status_code

    def del_resource(self, resource_id):
        url = self.base + "jasset/asset/del/?id={}".format(resource_id)
        res = requests.get(url=url, cookies=self.cookie)
        return res.status_code

    def search_resource(self, hostname):
        url = self.base + "jasset/asset/search/?hostname={}".format(hostname)
        res = requests.get(url=url, cookies=self.cookie)

        data = res.json()

        if not data:
            return None, None
        data = data[0]
        resource_id = data['pk']
        resource_data = data['fields']
        return resource_id, resource_data

    def edit_resource(self, resource_id, data):
        url = self.base + "jasset/asset/edit/?id={}".format(resource_id)
        res = requests.post(url=url, data=data, cookies=self.cookie)
        return res.status_code


if __name__ == "__main__":
    js = JumpServer("your username", "your passowrd", base="http://jump.t.nxin.com")
    print(js.add_resource("host1", "root", "root123", 22))
