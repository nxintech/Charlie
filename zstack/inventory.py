import os
import ujson as json
import pickle
import hashlib
import argparse
import datetime
from collections import defaultdict

from zssdk import configure, \
    LogInByUserAction, QueryVmInstanceAction, \
    QuerySystemTagAction, QueryUserTagAction, \
    AbstractAction, ParamAnnotation


def parse_date(string):
    """
    >>> parse_date('Nov 20, 2017 1:20:37 PM')
    datetime.datetime(2017, 11, 20, 13, 20, 37)
    """
    return datetime.datetime.strptime(string, '%b %d, %Y %I:%M:%S %p')


class LoginActionWrapper:
    """
    A Zstack LogInByUserAction Wrapper which cache session uuid that
    is not expired, for avoiding allocating too much session uuid.
    """

    def __init__(self, account, username, password):
        self.uuid = None
        self.expired = datetime.datetime.now()

        action = LogInByUserAction()
        action.accountName = account
        action.userName = username
        action.password = hashlib.sha512(password.encode('utf-8')).hexdigest()
        self.action = action

    def get_uuid(self):
        if self.is_expired_after_seconds(5):
            # we need renew a uuid
            response = self.action.call()
            if response.error:
                raise ValueError(response.error.details)
            if response.value:
                self.expired = parse_date(response.value.inventory.expiredDate)
                self.uuid = response.value.inventory.uuid

        return self.uuid

    def is_expired_after_seconds(self, n):
        now = datetime.datetime.now()
        # uuid is valid if it can be expired in n seconds later
        later = now + datetime.timedelta(seconds=n)
        return later > self.expired


def get_instances(limit=100):
    query.replyWithCount = True
    query.limit = limit
    query.start = 0
    total = 0
    count = 0

    while query.start == 0 or count < total:
        response = query.call(dict_output=True, debug=args.debug)
        if "error" in response:
            raise ValueError(response["error"]["details"])

        value = response["value"]
        total = value["total"]
        instances = value["inventories"]

        for instance in instances:
            yield instance

        count += len(instances)
        query.start += query.limit


def inventory_data():
    result = defaultdict(list)
    result['_meta'] = {'hostvars': {}}
    maps = {}  # {hostname: uuid} maps

    for instance in get_instances():
        hostname = instance["name"]
        maps[hostname] = instance["uuid"]

        if instance["state"] == "Destroyed":
            continue

        result['all'].append(hostname)
        result['_meta']['hostvars'][hostname] = {
            'ansible_ssh_user': "root",
            'ansible_ssh_host': instance["vmNics"][0]["ip"],
            'ansible_ssh_port': 22,
            'zstack': instance
        }

    # host aggregate by user tag
    for tag in get_user_tags():
        for instance in get_instances():
            hostname = instance["name"]

            if instance["state"] == "Destroyed":
                continue

            result[tag].append(hostname)

    return result, maps


def get_system_tags():
    q = QuerySystemTagAction()
    q.conditions = ["inherent=true", "resourceType=VmInstanceVO"]
    q.fields = ["tag"]
    q.sessionId = login.get_uuid()
    response = q.call(dict_output=True, debug=args.debug)

    if "error" in response:
        raise ValueError(response["error"]["details"])

    for tag in response["value"]["inventories"]:
        yield tag["tag"]


def get_user_tags():
    q = QueryUserTagAction()
    q.conditions = ["resourceType=VmInstanceVO"]
    q.fields = ["tag"]
    q.sessionId = login.get_uuid()
    response = q.call(dict_output=True, debug=args.debug)

    if "error" in response:
        raise ValueError(response["error"]["details"])

    for tag in response["value"]["inventories"]:
        yield tag["tag"]


def get_host(hostname):
    class QueryOneVmInstance(AbstractAction):
        HTTP_METHOD = 'GET'
        PATH = '/vm-instances/{uuid}'
        NEED_SESSION = True
        NEED_POLL = False
        PARAM_NAME = ''
        PARAMS = {
            'uuid': ParamAnnotation(
                required=True, non_empty=False,
                null_elements=False, empty_string=True,
                no_trim=False),
            'sessionId': ParamAnnotation(required=True)
        }

        def __init__(self):
            super(QueryOneVmInstance, self).__init__()
            self.uuid = None
            self.sessionId = None

    if not os.path.exists(".cache"):
        d, maps = inventory_data()
        with open(".cache", 'wb') as f:
            pickle.dump(maps, f)

        return d['_meta']['hostvars'][hostname] or {}

    with open(".cache", 'rb') as f:
        unpickler = pickle.Unpickler(f)
        maps = unpickler.load()
        if not isinstance(maps, dict):
            raise ValueError()

    q = QueryOneVmInstance()
    q.uuid = maps[hostname]
    q.sessionId = login.get_uuid()
    response = q.call(dict_output=True, debug=args.debug)

    if "error" in response:
        return {}

    instance = response["value"]["inventories"][0]
    host_vars = {
        'ansible_ssh_user': "root",
        'ansible_ssh_host': instance["vmNics"][0]["ip"],
        'ansible_ssh_port': 22,
        'zstack': instance
    }
    return host_vars


def parse_args():
    parser = argparse.ArgumentParser(description="Zstack Dynamic Inventory")
    # ansible dynamic inventory args
    g = parser.add_mutually_exclusive_group()
    g.add_argument('--list', action='store_true',
                   help='list all servers, conflict with --host')
    g.add_argument('--host',
                   help='list details about the specific hostname')

    parser.add_argument('--debug', action='store_true',
                        help='show request/response info')

    return parser.parse_args()


if __name__ == '__main__':
    # global settings
    configure(hostname="you api server")
    login = LoginActionWrapper("account", "username", "password")
    query = QueryVmInstanceAction()
    query.conditions = ["type=UserVm"]  # only query VmInstance
    query.sessionId = login.get_uuid()

    args = parse_args()
    if args.list:
        data, maps = inventory_data()
        with open(".cache", 'wb') as f:
            pickle.dump(maps, f)
        print(json.dumps(data, indent=2))

    if args.host:
        print(json.dumps(get_host(args.host), indent=2))
