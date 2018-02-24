# -*- coding:utf-8 -*-
"""
<Storage {
  'owner': None,
  'id': 10,
  'name': 'zntapi',
  'buildInfo': {
    'lang': 1, // 1 java| 2 .net | 3 python | 4 go
    'langVersion': 'jdk7',
    'repo': 'http://gitlab.dbn.cn/mobile/SERVER_ZNT_API.git',
    'repoType': 1,  # 1=git,2=svn
    'buildTool': 1, # 1=gradle,2=maven
    'buildCmd': 'clean prod war',
    'deployCmd': 'ssh root@10.211.19.6 /data0/script/deploy.sh;ssh root@10.211.19.7 /data0/script/deploy.sh',
    'moduleName': '',
    'packageType': 0 notset| 1 jar| 2 war
   },
  'hostNames': None,
  'description': '智农通接口',
  'domains': None
}>
"""
from __future__ import unicode_literals
import json
import pprint
import base64
import requests
import datetime
from enum import IntEnum
from functools import wraps
from future.moves.urllib.parse import urljoin


__all__ = ['Client', 'Project', 'BuildInfo', 'Language', 'RepoType', 'BuildTool', 'PackageType']

pp = pprint.PrettyPrinter(indent=2)


def print_debug_info(resp):
    print("============ Request ============")
    print("url: {} {}".format(resp.request.method, resp.request.url))
    print("header: {}".format(resp.request.headers))
    if resp.request.body:
        print("body: {}".format(resp.request.body))
    print("\n============ Response  ============")
    print("header: {}".format(resp.headers))
    print("status: {}".format(resp.status_code))
    print("body: '{}'".format(resp.text))
    print()


def require_token(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self._extra_headers = {"Private-Token": self.token}
        resp = func(self, *args, **kwargs)
        self._extra_headers = None
        return resp

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

        >>> o = Storage(a=1)
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


class Language(IntEnum):
    default = 0
    java = 1
    dotnet = 2
    python = 3
    golang = 4


class RepoType(IntEnum):
    default = 0
    git = 1
    svn = 2


class BuildTool(IntEnum):
    default = 0
    gradle = 1
    maven = 2


class PackageType(IntEnum):
    default = 0
    jar = 1
    war = 2
    exe = 3


def decode_hook(dct):
    s = Storage(dct)
    if 'buildInfo' in dct:
        build_info = dct['buildInfo']
        if 'lang' in build_info:
            s.buildInfo.lang = Language(build_info['lang'])
        if 'repoType' in build_info:
            s.buildInfo.repoType = RepoType(build_info['repoType'])
        if 'buildTool' in build_info:
            s.buildInfo.buildTool = BuildTool(build_info['buildTool'])
        if 'packageType' in build_info:
            s.buildInfo.packageType = BuildTool(build_info['packageType'])
    return s


class Project(Storage):
    def __init__(self, name, description, build_info, *, id=0, hostnames=None, domains=None):
        super().__init__()
        # Server will auto assign an id for a new project
        # But server needs the key <id> in body, so
        # We set value 0 to satisfy the requirement
        self.id = id
        self.owner = None
        self.name = name
        self.description = description
        self.hostNames = hostnames
        self.domains = domains
        self.buildInfo = build_info


class BuildInfo(Storage):
    def __init__(self, repo, repo_type, *, language=Language.default, lang_version=None, build_tool=BuildTool.default,
                 build_cmd=None, module=None, deploy_cmd=None, package_type=PackageType.default):
        super().__init__()
        self.repo = repo
        self.repoType = RepoType(repo_type)
        self.lang = Language(language)
        self.langVersion = lang_version
        self.buildTool = BuildTool(build_tool)
        self.buildCmd = build_cmd
        self.deployCmd = deploy_cmd
        self.moduleName = module
        self.packageType = PackageType(package_type)


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

    def _request(self, url, method='GET', json=None, **kwargs):
        kwargs.update({"json": json})
        if self._extra_headers is not None:
            kwargs["headers"] = self._extra_headers

        resp = requests.request(method, url, **kwargs)
        if self.debug:
            print_debug_info(resp)

        if not resp.ok:
            # error that status != 200
            raise ValueError(resp.text)

        data = resp.json(object_hook=decode_hook)
        if data['code'] != 0:
            # error that status = 200
            raise ValueError(data)

        return data["data"]

    @property
    def token(self):
        def is_token_expired():
            now = datetime.datetime.now()
            # token expired in 5 seconds later
            # is treated as expired as well
            later = now + datetime.timedelta(seconds=5)
            ts = later.replace().timestamp()
            return ts > self._token_expired.replace().timestamp()

        if self._token is None or is_token_expired():
            self.get_token()

        return self._token

    def get_token(self):
        endpoint = "/api/v1/auth/token"
        url = urljoin(self.api_base_url, endpoint)
        data = self._request(url, method='POST', json={
            "username": self.username,
            "password": self.password
        })
        self._token = data["token"]
        self._token_expired = parse_date(data["expired"])

    def parse_token(self):
        b = base64.b64decode(self._token.split('.')[1])
        return json.loads(b.decode('utf-8'))

    @require_token
    def get_projects(self):
        endpoint = "/api/v1/projects/{}"
        url = urljoin(self.api_base_url, endpoint)
        return self._request(url)

    @require_token
    def get_project(self, name):
        endpoint = "/api/v1/projects/{}".format(name)
        url = urljoin(self.api_base_url, endpoint)
        return self._request(url)

    @require_token
    def get_project_package(self, name):
        endpoint = "/api/v1/projects/{}/package".format(name)
        url = urljoin(self.api_base_url, endpoint)
        return self._request(url)

    @require_token
    def get_project_members(self, name):
        endpoint = "/api/v1/projects/{}/members".format(name)
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

    @require_token
    def add_project(self, project):
        project.owner = self.parse_token()['boId']
        endpoint = "/api/v1/projects"
        url = urljoin(self.api_base_url, endpoint)
        return self._request(url, method='POST', json=project)

    @require_token
    def update_project(self, project):
        endpoint = "/api/v1/projects/"
        url = urljoin(self.api_base_url, endpoint)
        return self._request(url, method='PUT', json=project)

    @require_token
    def get_user(self, username):
        endpoint = "/api/v1/users/{}".format(username)
        url = urljoin(self.api_base_url, endpoint)
        return self._request(url)

    @require_token
    def get_user_projects(self, username):
        endpoint = "/api/v1/users/{}/projects/".format(username)
        url = urljoin(self.api_base_url, endpoint)
        return self._request(url)

    @require_token
    def search_user(self, params):
        # { "id": "name": username}
        endpoint = "/api/v1/search/users"
        url = urljoin(self.api_base_url, endpoint)
        return self._request(url, params=params)
