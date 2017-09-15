# -*- coding:utf-8 -*-
import requests


class JumpServer(object):
    def __init__(self, username, password, url="http://jump.t.nxin.com/"):
        self._cookie = None
        self.username = username
        self.password = password
        self.url = url

    def get_cookie(self):
        if not self._cookie:
            url = self.url + "login/"
            data = {
                "username": self.username,
                "password": self.password
            }
            res = requests.post(url=url, data=data)
            self._cookie = res.cookies
        return self._cookie

    def add_resource(self, hostname, username, password,
                     port, ip=None, group=None, is_active=1):
        url = self.url + "jasset/asset/add/"
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


if __name__ == "__main__":
    js = JumpServer("your username", "your passowrd")
    print(js.add_resource("host1", "root", "root123", 22))
