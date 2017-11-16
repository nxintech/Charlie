import json
import requests
import urllib
import six

if six.PY3:
    urljoin = urllib.parse.urljoin
else:
    from urlparse import urljoin


# https://github.com/1046102779/prometheus/blob/master/querying/http_api.md

def parse_result(response):
    data = json.loads(response.text)
    if data["status"] == "success":
        return data["data"]["result"]
    else:
        print(response.text)


class Wrapper(object):
    def __init__(self, prefix):
        self.prefix = prefix

    def query(self, selector, time=None, timeout=None):
        params = {"query": selector}
        if time:
            params["time"] = time
        if timeout:
            params["timeout"] = timeout

        uri = urljoin(self.prefix, "query")
        resp = requests.get(uri, params=params)
        return parse_result(resp)

    def query_range(self, selector, start, end, step):
        uri = urljoin(self.prefix, "query_range")
        params = {
            "query": selector,
            "start": start,
            "end": end,
            "step": step
        }
        resp = requests.get(uri, params=params)
        return parse_result(resp)


FORMAT = "%Y-%m-%d %H:%M:%S"
query = Wrapper("http://prometheus.nxin.com/api/v1/")

r = query.query("nginx_http_requests_total{host=\"zjs.nxin.com\"}", time="2017-11-15T13:00:00+08:00")
print(r)
