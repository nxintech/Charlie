# -*- coding:utf-8 -*-
"""
<Storage {
  'owner': None,
  'id': 10,
  'name': 'zntapi',
  'buildInfo': {
    'lang': 1,
    'repo': 'http://gitlab.dbn.cn/mobile/SERVER_ZNT_API.git',
    'repoType': 1,  # 1=git,2=svn
    'buildTool': 1, # 1=gradle,2=maven
    'buildCmd': 'clean prod war',
    'deployCmd': 'ssh root@10.211.19.6 /data0/script/deploy.sh;ssh root@10.211.19.7 /data0/script/deploy.sh',
    'langVersion': 'jdk7',
    'moduleName': '',
    'packageType': 2
   },
  'hostNames': None,
  'description': '智农通接口',
  'domains': None
}>
"""
from __future__ import unicode_literals
import pprint
import requests
import datetime
from functools import wraps
from future.moves.urllib.parse import urljoin

pp = pprint.PrettyPrinter(indent=2)


def print_debug_info(resp):
    print("\n============ Request ============")
    print("uri: {}".format(resp.request.path_url))
    print("header:")
    pp.pprint(resp.request.headers)
    if resp.request.body:
        print("\nbody:")
        pp.pprint(resp.request.body)
    print("\n============ Response  ============")
    print("header:")
    pp.pprint(resp.headers)
    print("\nstatus: {}".format(resp.status_code))
    print("response:")
    pp.pprint(resp.text)
    print()


def require_token(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self._extra_headers = {"Private-Token": self.token}
        return func(self, *args, **kwargs)

    return wrapper


def parse_date(rfc3339):
    """
    >>> parse_date('2017-12-19T11:21Z')
    datetime.datetime(2017, 12, 19, 11, 21, 41)
    """
    if rfc3339.endswith('Z'):
        # remove Z
        rfc3339 = rfc3339[:-1] + '+0000'

    elif '+' in rfc3339:
        time_str, zone = rfc3339.split('+')
        # remove colon in zone
        rfc3339 = time_str + '+' + zone.replace(':', '')

    return datetime.datetime.strptime(rfc3339, '%Y-%m-%dT%H:%M:%S%z')


class Storage(dict):
    """
    borrow from web.py
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.

        >>> o = storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'

    """
    def __init__(self, d, **kwargs):
        super().__init__(**kwargs)
        for k, v in d.items():
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as e:
            raise AttributeError(e)

    def __repr__(self):
        return '<Storage ' + dict.__repr__(self) + '>'


class Client:
    def __init__(self,
                 username=None,
                 password=None,
                 base="http://proj.nxin.com",
                 debug=False):
        self.username = username
        self.password = password
        self.api_base_url = base
        self.debug = debug

        self._token = None
        self._token_expired = None
        self._extra_headers = None

    def _request(self, url, method='GET', json=None):
        kwargs = {"json": json}
        if self._extra_headers is not None:
            kwargs["headers"] = self._extra_headers

        resp = requests.request(method, url, **kwargs)
        if self.debug:
            print_debug_info(resp)

        if not resp.ok:
            # error that status != 200
            raise ValueError(resp.text)

        data = resp.json()
        if data['code'] != 0:
            # error that status = 200
            raise ValueError(data)

        return data["data"]

    @property
    def token(self):
        if self._token is None or self._is_token_expired():
            self.get_token()
        return self._token

    def _is_token_expired(self):
        now = datetime.datetime.now()
        # token expired in 5 seconds later
        # is treated as expired as well
        later = now + datetime.timedelta(seconds=5)
        return later > self._token_expired

    def get_token(self):
        endpoint = "/api/v1/auth/token"
        url = urljoin(self.api_base_url, endpoint)
        data = self._request(url, method='POST', json={
            "username": self.username,
            "password": self.password
        })
        self._token = data["token"]
        self._token_expired = data["expired"]

    @require_token
    def get_projects(self):
        endpoint = "/api/v1/projects"
        url = urljoin(self.api_base_url, endpoint)
        return [Storage(project) for project in self._request(url)]

    @require_token
    def get_project(self, id_or_name):
        url = self._project_endpoint(id_or_name)
        project = self._request(url)
        return Storage(project)

    @require_token
    def get_project_package(self, name):
        endpoint = "/api/v1/projects/getPackage/{}".format(name)
        url = urljoin(self.api_base_url, endpoint)
        return self._request(url)

    @require_token
    def get_project_members(self, id):
        endpoint = "/api/v1/projects/members/{}".format(id)
        url = urljoin(self.api_base_url, endpoint)
        return self._request(url)

    @require_token
    def delete_project(self, id_or_name):
        url = self._project_endpoint(id_or_name)
        return self._request(url, method='delete')

    def _project_endpoint(self, id_or_name):
        if isinstance(id_or_name, str):
            endpoint = "/api/v1/projects/{}".format(id_or_name)
            return urljoin(self.api_base_url, endpoint)
        elif isinstance(id_or_name, str):
            endpoint = "/api/v1/projects/id/{}".format(id_or_name)
            return urljoin(self.api_base_url, endpoint)
        else:
            raise TypeError("Type of argument should be 'int' or 'str'")

    # TODO
    # @require_token
    # def add_project(self, name, description, hostnames=None, domains=None, build_info=None):
    #     endpoint = "/api/v1/projects/"
    #     url = urljoin(self.api_base_url, endpoint)
    #     return self._request(url, method='POST', json={
    #         # Server will auto assign an id for a new project
    #         # But server needs the key <id> in body, so
    #         # We set value 0 to satisfy the requirement
    #         "id": 0,
    #         "name": name,
    #         "description": description,
    #         "hostNames": hostnames,
    #         "domains": domains,
    #         "buildInfo": build_info
    #     })

    # TODO
    # @require_token
    # def update_project(self, project):
    #     endpoint = "/api/v1/projects/"
    #     url = urljoin(self.api_base_url, endpoint)
    #     return self._request(url, method='PUT', json={project})

    @require_token
    def get_user(self, username):
        endpoint = "/api/v1/users/{}".format(username)
        url = urljoin(self.api_base_url, endpoint)
        user = self._request(url)
        return Storage(user)

    @require_token
    def get_user_projects(self, username):
        endpoint = "/api/v1/users/{}/projects/".format(username)
        url = urljoin(self.api_base_url, endpoint)
        return [Storage(p) for p in self._request(url)]
