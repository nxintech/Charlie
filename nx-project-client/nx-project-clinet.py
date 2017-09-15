# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import requests

Domain = "http://proj.nxin.com"


def get_all():
    return requests.post("{}/app/getAll".format(Domain)).json()


def get_project_by_name(name):
    return requests.post("{}/app/getByName".format(Domain), data={"name": name}).json()


def add_project(data, sync=False):
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
    return requests.post("{}/app/update/{}".format(Domain, int(sync)), data=data).json()


# test
# print(get_all())
print(get_project_by_name("zntapi"))


# data = {
#     "id": "",
#     "appId": "999",
#     "name": "test_fuck",
#     "description": "test",
#     "repo": "",
#     "repoType": "1",
#     "buildType": "1",
#     "moduleName": "",
#     "task": "",
#     "script": "",
#     "ip": ""
# }
#
# print(add_project(
#     {
#         "appId": 999,
#         "name": "test_project",
#         "buildType": 1
#     }, False))