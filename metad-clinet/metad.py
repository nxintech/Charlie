# -*- coding:utf-8 -*-
import requests
import functools
from types import MethodType

def get(self, key=None, params=None, accept="application/json"):
    if params is None:
        params = {"pretty": True}
    if key:
        url = "{}/{}".format(self.path, key)
    else:
        url = self.url
    resp = requests.get(url, headers={"Accept": accept}, params=params)
    return resp.text


def func_factory(method):
    func = getattr(requests, method)

    @functools.wraps(func)
    # wraps replace argument "method" as the method name of bound class 
    # e.g "<bound method <method> of <class name>" will be instead of
    # "<bound method update.<locals>.caller of <class name>"
    def callee(self, data, key=None):
        if key:
            url = "{}/{}".format(self.path, key)
        else:
            url = self.url
        resp = func(url, json=data)
        return resp.text
    return callee

post = func_factory("post")
put = func_factory("put")


def delete(self, key):
    url = "{}/{}".format(self.path, key)
    resp = requests.delete(url)
    return resp.text


class Data(object):
    def __init__(self, url):
        self.url = "{}/v1/data".format(url)


class Mapping(object):
    def __init__(self, url):
        self.url = "{}/v1/mapping".format(url)


class Metad(object):
    def __init__(self, host="127.0.0.1", port="9611"):
        self.url = "http://{}:{}".format(host, port)
        self.get = MethodType(get, self)

        self.data = Data(self.url)
        self.data.get = MethodType(get, self.data)
        self.data.post = MethodType(post, self.data)
        self.data.put = MethodType(put, self.data)
        self.data.delete = MethodType(delete, self.data)

        self.mapping = Mapping(self.url)
        self.mapping.get = MethodType(get, self.mapping)
        self.mapping.post = (post, self.mapping)
        self.mapping.put = (put, self.mapping)
        self.mapping.delete = (delete, self.mapping)

