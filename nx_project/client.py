# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import json
import http.cookiejar
import urllib.request
from functools import wraps
from urllib.parse import urlencode


def check_error(data):
    if data['code'] != 0:
        raise ValueError(data)
    return data


def authenticate(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        token = False
        for cookie in self.cookie:
            if cookie.name == 'projToken':
                token = True
        if not token:
            self._authenticate()
        data = func(self, *args, **kwargs)
        return check_error(data)

    return wrapper


class Proj:
    def __init__(self,
                 username=None,
                 password=None,
                 base="http://proj.nxin.com"):
        self.username = username
        self.password = password
        self.base = base

        self.cookie = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie))

    def _authenticate(self):
        url = "{}/user/authenticate".format(self.base)
        data = urlencode({
            "username": self.username,
            "password": self.password}).encode()
        req = urllib.request.Request(url, data=data, method='POST')
        response = self.opener.open(req)
        data = json.loads(response.read().decode('utf-8'))
        check_error(data)

    @authenticate
    def get_all(self):
        url = "{}/app/getAll".format(self.base)
        req = urllib.request.Request(url, method='POST')
        response = self.opener.open(req)
        data = json.loads(response.read().decode('utf-8'))
        return check_error(data)

    @authenticate
    def get_by_page(self, page_index=1, page_size=10):
        url = "{}/app/getByPage".format(self.base)
        data = urlencode({
            "pageIndex": page_index,
            "pageSize": page_size}).encode()
        req = urllib.request.Request(url, data=data, method='POST')
        response = self.opener.open(req)
        data = json.loads(response.read().decode('utf-8'))
        return data

    @authenticate
    def get_by_name(self, name):
        url = "{}/app/getByName".format(self.base)
        data = urlencode({"name": name}).encode()
        req = urllib.request.Request(url, data=data, method='POST')
        response = self.opener.open(req)
        data = json.loads(response.read().decode('utf-8'))
        return data

    # TODO
    def add_project(self, data, sync=False):
        """
        data JSON格式：
        {
            "id",
            "appId",           # 应用ID
            "name",            # 应用名称
            "secret",          # do not post this field
            "repo",            # 仓库地址
            "repoType",        # 仓库类型 1=git,2=svn
            "buildType",       # 1=gradle,2=maven
            "ip",              # hostname1,hostname2...
            "jdkVersion",      # 只能是 jdk7/jdk8
            "validationType",  # 永远是0,表示简单认证方式
            "description",     # 描述
            "moduleName",
            "task",            # clean prod war
            "script",

        }

        example:
        data = {
            "appId": 999,
            "name": "test_project",
            "buildType": 1
        }

        sync              # 0=不同步到jenkins,1=同步
        """
        pass
        # return requests.post("{}/app/update/{}".format(domain, int(sync)), data=data).json()


# test
p = Proj(username='user', password='passwd')
print(p.get_all())
print(p.get_by_page())
