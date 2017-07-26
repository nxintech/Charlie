# -*- coding:utf-8 -*-
import urllib3
import simplejson as json


class Config:
    """ Default config """
    host = '127.0.0.1'
    port = 8080
    manage_port = 9611
    version_prefix = '/v1/'
    protocol = 'http'
    read_timeout = 60
    per_host_pool_size = 5


def _response(response):
    raw_response = response.data
    try:
        res = json.loads(raw_response.decode('utf-8'))
        return response.getheaders(), res
    except (TypeError, ValueError, UnicodeError) as e:
        raise Exception('Server response was not valid JSON: %r' % e)


class BaseClient(object):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'

    def __init__(
            self,
            host=Config.host,
            port=Config.port,
            version_prefix=Config.version_prefix,
            protocol=Config.protocol,
            read_timeout=Config.read_timeout,
            per_host_pool_size=Config.per_host_pool_size
    ):
        """
        Initialize the client.
        """

        self._protocol = protocol
        self._read_timeout = read_timeout

        kw = {
            'maxsize': per_host_pool_size
        }

        if self._read_timeout > 0:
            kw['timeout'] = self._read_timeout

        self.http = urllib3.PoolManager(num_pools=10, **kw)

        def uri(protocol, host, port):
            return '%s://%s:%d' % (protocol, host, port)

        self._base_uri = uri(self._protocol, host, port)

        self.version_prefix = version_prefix

    @property
    def base_uri(self):
        return self._base_uri

    @property
    def protocol(self):
        return self._protocol

    @property
    def read_timeout(self):
        return self._read_timeout

    def get(self, path="", **kwargs):
        path = self.version_prefix + path

        params = {}
        for (k, v) in kwargs.items():
            if type(v) == bool:
                params[k] = v and "true" or "false"
            elif v is not None:
                params[k] = v
        timeout = kwargs.get('timeout', self._read_timeout)

        response = self._execute(self.GET, path, params=params, timeout=timeout)
        return _response(response)

    def _execute(self, method, path, params=None, timeout=None):
        url = self._base_uri + path
        json_payload = json.dumps(params)
        headers = {'Accept': 'application/json'}

        if method == self.GET or method == self.DELETE:
            return self.http.request(
                method,
                url,
                timeout=timeout,
                fields=params,
                headers=headers,
                preload_content=False
            )

        if method == self.POST or method == self.PUT:
            return self.http.urlopen(
                method,
                url,
                body=json_payload,
                timeout=timeout,
                headers=headers,
                preload_content=False)


class Client(BaseClient):
    def __init__(
            self,
            host=Config.host,
            port=Config.port,
            manage_port=Config.manage_port,
            version_prefix=Config.version_prefix,
            protocol=Config.protocol,
            read_timeout=Config.read_timeout,
            per_host_pool_size=Config.per_host_pool_size
    ):
        super().__init__(host, port, version_prefix, protocol, read_timeout, per_host_pool_size)
        self.map = BaseClient(host, manage_port, version_prefix + 'map/',
                              protocol, read_timeout, per_host_pool_size)
        self.mapping = BaseClient(host, manage_port, version_prefix + 'mapping/',
                                  protocol, read_timeout, per_host_pool_size)
        self.data = BaseClient(host, manage_port, version_prefix + 'data/',
                               protocol, read_timeout, per_host_pool_size)

    def __del__(self):
        """Clean up open connections"""
        if self.http is not None:
            try:
                self.http.clear()
                self.mapping.http.clear()
                self.map.http.clear()
                self.data.http.clear()
            except ReferenceError:
                # this may hit an already-cleared weakref
                pass
