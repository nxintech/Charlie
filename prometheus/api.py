import json
import requests


class Wrapper(object):
    def __init__(self, prefix):
        self.prefix = prefix

    def get(self, uri, *args, **kwargs):
        data = json.loads(requests.get(self.prefix + uri, *args, **kwargs).text)["data"]
        return data["result"]


request = Wrapper("http://prometheus.nxin.com/api/v1/query?query=")

print(request.get("rate(mysql_slave_status_seconds_behind_master[1m])"))