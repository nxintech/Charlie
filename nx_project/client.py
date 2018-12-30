# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import json
import http.client


class Proj:
    def __init__(self,
                 username=None,
                 password=None,
                 base="proj.nxin.com"):
        self.username = username
        self.password = password
        self.conn = http.client.HTTPConnection(base)
        self.token = self.login()

    def login(self):
        data = {
            "username": self.username,
            "password": self.password}
        data = self.post('/api/v1/auth/token', data, require_auth=False)
        return data['data']['token']

    def get(self, uri, require_auth=True):
        return self.request('GET', uri, require_auth)

    def post(self, uri, data, require_auth=True):
        body = json.dumps(data).encode()
        return self.request('POST', uri, require_auth, body)

    def request(self, method, uri, require_auth, body=None, headers=None):
        method = method.upper()
        if isinstance(headers, dict):
            headers['Content-Type'] = 'application/json'
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        if require_auth:
            headers['Private-Token'] = self.token

        self.conn.request(method, uri, body, headers)
        resp = self.conn.getresponse()
        if 299 < resp.status < 200:
            raise ValueError(resp)
        data = json.loads(resp.read())
        if data['code'] != 0:
            raise ValueError(data)
        return data

    def get_projects(self):
        data = self.get('/api/v1/projects')
        return data['data']

    def get_project(self, name):
        data = self.get('/api/v1/projects/{}'.format(name))
        return data['data']

# test
# p = Proj(username='admin', password='xxxxx')
# print(p.get_project('oa'))
