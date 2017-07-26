# -*- coding:utf-8 -*-
import requests


class Client(object):
    def __init__(
            self,
            host='127.0.0.1',
            port=8080,
            manage_port=9611,
            version_prefix='/v1/',
            protocol='http',
            read_timeout=60
    ):
        """
        Initialize the client.
        """

        self._protocol = protocol
        self._read_timeout = read_timeout
        self.version_prefix = version_prefix
        self._base_uri = '%s://%s:%d' % (self._protocol, host, port)
        self._manage_base_uri = '%s://%s:%d' % (self._protocol, host, manage_port)

    @property
    def base_uri(self):
        return self._base_uri

    @property
    def manage_base_uri(self):
        return self._manage_base_uri

    @property
    def protocol(self):
        return self._protocol

    @property
    def read_timeout(self):
        return self._read_timeout

    def mget(self, path="", params=None, headers=None):
        uri = self.version_prefix + path
        if headers is None:
            headers = {}
        headers.update({'Accept': 'application/json'})
        response = requests.get(self.manage_base_uri + uri,
                                params=params, headers=headers, timeout=self.read_timeout)

        return response.json()

    def mput(self, path, data, headers=None):
        uri = self.version_prefix + path
        if headers is None:
            headers = {}
        headers.update({'Content-Type': 'application/json'})

        response = requests.put(self.manage_base_uri + uri, json=data, headers=headers, timeout=self.read_timeout)
        return response.text

    def mdelete(self, path, params=None, headers=None):
        uri = self.version_prefix + path
        response = requests.delete(self.manage_base_uri + uri,
                                   params=params, headers=headers, timeout=self.read_timeout)
        return response.text
