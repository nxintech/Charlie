import aiohttp
import asyncio
import hashlib
import datetime
import async_timeout

try:
    import ujson as json
except ModuleNotFoundError:
    import json
from uuid import uuid4
from urllib.parse import urljoin


def raise_error(status, body):
    raise ValueError("status {}, message {}".format(status, body))


def uuid():
    return str(uuid4()).replace('-', '')


def parse_date(string):
    """
    >>> parse_date('Nov 20, 2017 1:20:37 PM')
    datetime.datetime(2017, 11, 20, 13, 20, 37)
    """
    return datetime.datetime.strptime(string, '%b %d, %Y %I:%M:%S %p')


def replace(s, obj):
    """
    >>> obj.uuid = 'zstack'
    >>> obj.Xy = 'Yx'
    >>> replace('test/{uuid}/{Xy}/abc', obj)
    'test/zstack/Yx/abc'

    >>> replace('test/no/variables', obj)
    'test/no/variables'

    >>> replace('test/{uuid}/{Xy}/{abc}', obj)
    ValueError: missing a mandatory parameter[abc]
    """

    def find_var(s):
        """
        >>> find_var('test/{uuid}/{Xy}/abc')
        ['uuid', 'Xy']
        """
        result = []
        match = False
        for c in s:
            if match:
                if c == '}':
                    result.append("".join(word))
                    match = False
                else:
                    word.append(c)

            if c == '{':
                match = True
                word = []
        return result

    m = {}
    for name in find_var(s):
        value = getattr(obj, name, None)
        if value is None:
            raise ValueError('missing a mandatory parameter[%s]' % name)

        m[name] = value

    return s.format(**m)


class TaskPool:
    def __init__(self, max_threads=10, loop=None):
        self.semaphore = asyncio.Semaphore(max_threads)
        self.loop = loop or asyncio.get_event_loop()
        self.tasks = []

    def run(self):
        self.loop.run_until_complete(asyncio.wait(self.tasks))

    async def add_task(self, task):
        with (await self.semaphore):
            await self.process_task(task)

    async def process_task(self, task):
        raise NotImplementedError


class Session:
    session_available_time_from_now = 10

    def __init__(self, account, username, password, client):
        self._account = account
        self._username = username
        self._password = password
        self.client = client

        self.session_id = None
        self.session_expired_at = datetime.datetime.now()

    async def get_session_id(self):
        if self._session_is_expired_after_seconds(
                self.session_available_time_from_now):
            # we need renew session id
            login = LogInByUserAction(
                account_name=self._account,
                username=self._username,
                password=hashlib.sha512(
                    self._password.encode('utf-8')).hexdigest())

            json_body = await self.client.request_action(login)

            # json_body = json.loads(body)
            inventory = json_body['value']['inventory']
            self.session_expired_at = parse_date(inventory['expiredDate'])
            self.session_id = inventory['uuid']

        return self.session_id

    async def logout(self):
        if self.session_id is None:
            return
        if self._session_is_expired_after_seconds(
                self.session_available_time_from_now):
            # session will expired in 10 sec, do nothing
            # let session expired at server side
            self.session_id = None
            return

        logout = LogOutAction(session_id=self.session_id)
        # LogOutAction body is ''
        _ = await self.client.request_action(logout)

    def _session_is_expired_after_seconds(self, n):
        now = datetime.datetime.now()
        # uuid is valid if it can be expired in n seconds later
        later = now + datetime.timedelta(seconds=n)
        return later > self.session_expired_at


class ZStackClient(TaskPool):
    def __init__(self, loop=None,
                 host='127.0.0.1', port=80, request_timeout=10,
                 polling_timeout=30, polling_interval=5):
        """
        :param loop: event loop
        :param host: API Server host
        :param port: API Server port
        :param request_timeout: HTTP request timeout
        :param polling_timeout: Async API polling timeout
        :param polling_interval: Async API polling interval
        """
        super().__init__()
        self.loop = loop
        self._host = host
        self._port = port
        self._request_timeout = request_timeout
        self._polling_timeout = polling_timeout
        self._polling_interval = polling_interval

        self.session = None
        self._conn = aiohttp.TCPConnector(
            verify_ssl=False, limit=50, use_dns_cache=True)

    def set_session(self, account, username, password):
        self.session = Session(account, username, password, self)

    def _url(self, action):
        base = "http://{}:{}/{}".format(self._host, self._port, action.API_PATH)
        path = replace(action.PATH, action)
        path = path[1:] if action.PATH.startswith('/') else path
        return urljoin(base, path)

    async def process_task(self, task):
        pass

    async def request_action(self, action):
        headers, params, body = await self._prepare_request(action)

        status, body = await self._do_request(
            action.HTTP_METHOD, self._url(action),
            params=params, headers=headers, json=body)

        if body != '':
            json_body = json.loads(body)
        else:
            json_body = ''

        if status == 200 or status == 204:
            # API completes
            return {"value": json_body}

        elif status == 202:
            # API needs polling
            if action.NEED_POLL:
                return await self.poll(action, json_body)
            return {"value": json_body}

        else:
            raise_error(status, json_body)

    async def _prepare_request(self, action):
        # prepare headers
        headers = {"X-Job-UUID": uuid()}
        if action.NEED_SESSION:
            session_id = await self.session.get_session_id()
            headers.update({"Authorization": "OAuth {}".format(session_id)})

        # TODO web_hook support
        # if web_hook is not None:
        #     headers["webhook"] = web_hook

        # prepare params
        params = None
        if isinstance(action, QueryAction):
            params = action.query_params()

        # prepare body
        body = None
        if action.HTTP_METHOD in ('POST', 'PUT'):
            body = {action.PARAM_NAME: action.params()}

        return headers, params, body

    async def _do_request(self, method, url, **kwargs):
        with async_timeout.timeout(self._request_timeout):
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as resp:
                    return resp.status, await resp.text()

    async def poll(self, action, body):
        if not action.NEED_POLL:
            return raise_error(202, body)

        location = body['location']

        with async_timeout.timeout(self._polling_timeout):
            count = 0
            while True:
                status, body = await self._do_request('GET', location)
                if status in [200, 503]:
                    return {"value": json.loads(body)}

                count += 1
                await asyncio.sleep(self._polling_interval)

        # polling timeout
        return raise_error(500, "Location {} polling timeout, count: {}".format(location, count))

    async def close(self):
        await self.session.logout()


class ParamAnnotation(object):
    def __init__(
            self,
            required=False,
            valid_values=None,
            valid_regex_values=None,
            max_length=None,
            min_length=None,
            non_empty=False,
            null_elements=False,
            empty_string=True,
            number_range=None,
            no_trim=False,
            field='header'
    ):
        self.required = required
        self.valid_values = valid_values
        self.valid_regex_values = valid_regex_values
        self.max_length = max_length
        self.min_length = min_length
        self.non_empty = non_empty
        self.null_elements = null_elements
        self.empty_string = empty_string
        self.number_range = number_range
        self.no_trim = no_trim
        self.field = field


class AbstractAction:
    API_PATH = 'zstack/v1/'
    PATH = ''
    PARAM_NAME = ''
    HTTP_METHOD = ''
    NEED_POLL = False
    NEED_SESSION = False
    PARAMS = {}

    def __init__(self):
        self.check_attribute()

    def check_attribute(self):
        for name, annotation in self.PARAMS.items():
            value = getattr(self, name, None)

            if annotation.required and value is None:
                raise ValueError("attribute '{}' required but not set.".format(name))

            if value is None:
                continue

            if annotation.valid_values and value not in annotation.valid_values:
                raise ValueError(
                    "attribute {} not in the valid options{}."
                        .format(name, annotation.valid_values))

            if annotation.no_trim is False and isinstance(value, str):
                setattr(self, name, value.strip())

    def params(self):
        result = {}
        for k, _ in self.PARAMS.items():
            v = getattr(self, k, None)
            if v is not None:
                result[k] = v
        return result


class LogInByUserAction(AbstractAction):
    HTTP_METHOD = 'PUT'
    PATH = '/accounts/users/login'
    PARAM_NAME = 'logInByUser'
    NEED_SESSION = False
    NEED_POLL = False

    PARAMS = {
        'accountUuid': ParamAnnotation(),
        'accountName': ParamAnnotation(),
        'userName': ParamAnnotation(required=True),
        'password': ParamAnnotation(required=True),
        'systemTags': ParamAnnotation(),
        'userTags': ParamAnnotation()
    }

    def __init__(
            self,
            account_uuid=None,
            account_name=None,
            username=None,
            password=None,
            system_tags=None,
            user_tags=None
    ):
        self.accountUuid = account_uuid
        self.accountName = account_name
        self.userName = username
        self.password = password
        self.systemTags = system_tags
        self.userTags = user_tags
        super().__init__()


class LogOutAction(AbstractAction):
    HTTP_METHOD = 'DELETE'
    PATH = '/accounts/sessions/{sessionUuid}'
    NEED_SESSION = False
    NEED_POLL = False
    PARAM_NAME = ''

    PARAMS = {
        'sessionUuid': ParamAnnotation(),
        'systemTags': ParamAnnotation(),
        'userTags': ParamAnnotation()
    }

    def __init__(self, session_id=None):
        self.sessionUuid = session_id
        self.systemTags = None
        self.userTags = None
        super().__init__()


class QueryAction(AbstractAction):
    HTTP_METHOD = 'GET'

    PARAMS = {
        'conditions': ParamAnnotation(required=True),
        'limit': ParamAnnotation(),
        'start': ParamAnnotation(),
        'count': ParamAnnotation(),
        'groupBy': ParamAnnotation(),
        'replyWithCount': ParamAnnotation(),
        'sortBy': ParamAnnotation(),
        'sortDirection': ParamAnnotation(valid_values=['asc', 'desc']),
        'fields': ParamAnnotation(),
    }

    def __init__(
            self,
            conditions=None
    ):
        self.conditions = conditions or []
        self.limit = None
        self.start = None
        self.count = None
        self.groupBy = None
        self.replyWithCount = None
        self.sortBy = None
        self.sortDirection = None
        self.fields = None
        self.sessionId = None
        super().__init__()

    def query_params(self):
        params = []

        for name, attr in self.params().items():
            if attr is None:
                continue

            if name == "sortBy":
                if self.sortDirection is None:
                    params.append(("sort", attr))
                else:
                    op = '+' if attr == 'asc' else '-'
                    params.append(("sort", "{}{}".format(op, attr)))
            elif name == "sortDirection":
                continue

            elif name == "fields":
                params.append(("fields", ','.join(attr)))

            elif name == "conditions":
                for condition in attr:
                    params.append(('q', condition))

            else:
                attr = str(attr) if isinstance(attr, int) else attr
                params.append((name, attr))

        return params


class QueryVmInstanceAction(QueryAction):
    PATH = '/vm-instances'
    NEED_SESSION = True
    NEED_POLL = False
    PARAM_NAME = ''

    PARAMS = {
        'conditions': ParamAnnotation(required=True, non_empty=False, null_elements=False, empty_string=True,
                                      no_trim=False),
        'limit': ParamAnnotation(),
        'start': ParamAnnotation(),
        'count': ParamAnnotation(),
        'groupBy': ParamAnnotation(),
        'replyWithCount': ParamAnnotation(),
        'sortBy': ParamAnnotation(),
        'sortDirection': ParamAnnotation(required=False, valid_values=['asc', 'desc'], non_empty=False,
                                         null_elements=False, empty_string=True, no_trim=False),
        'fields': ParamAnnotation(),
        'systemTags': ParamAnnotation(),
        'userTags': ParamAnnotation(),
    }

    def __init__(self):
        self.conditions = None
        self.limit = None
        self.start = None
        self.count = None
        self.groupBy = None
        self.replyWithCount = None
        self.sortBy = None
        self.sortDirection = None
        self.fields = None
        self.systemTags = None
        self.userTags = None
        self.sessionId = None
        self.uuid = None
        super().__init__()


class QueryOneVmInstance(QueryAction):
    PATH = '/vm-instances/{uuid}'
    NEED_SESSION = True
    NEED_POLL = False
    PARAM_NAME = ''
    PARAMS = {}

    def __init__(self):
        self.uuid = None
        super().__init__()


class QuerySystemTagAction(QueryAction):
    PATH = '/system-tags'
    NEED_SESSION = True
    NEED_POLL = False
    PARAM_NAME = ''

    PARAMS = {
        'conditions': ParamAnnotation(required=True, non_empty=False, null_elements=False, empty_string=True,
                                      no_trim=False),
        'limit': ParamAnnotation(),
        'start': ParamAnnotation(),
        'count': ParamAnnotation(),
        'groupBy': ParamAnnotation(),
        'replyWithCount': ParamAnnotation(),
        'sortBy': ParamAnnotation(),
        'sortDirection': ParamAnnotation(required=False, valid_values=['asc', 'desc'], non_empty=False,
                                         null_elements=False, empty_string=True, no_trim=False),
        'fields': ParamAnnotation(),
        'systemTags': ParamAnnotation(),
        'userTags': ParamAnnotation(),
    }

    def __init__(self):
        self.conditions = None
        self.limit = None
        self.start = None
        self.count = None
        self.groupBy = None
        self.replyWithCount = None
        self.sortBy = None
        self.sortDirection = None
        self.fields = None
        self.systemTags = None
        self.userTags = None
        super().__init__()


class QueryUserTagAction(QueryAction):
    PATH = '/user-tags'
    NEED_SESSION = True
    NEED_POLL = False
    PARAM_NAME = ''

    PARAMS = {
        'conditions': ParamAnnotation(required=True, non_empty=False, null_elements=False, empty_string=True,
                                      no_trim=False),
        'limit': ParamAnnotation(),
        'start': ParamAnnotation(),
        'count': ParamAnnotation(),
        'groupBy': ParamAnnotation(),
        'replyWithCount': ParamAnnotation(),
        'sortBy': ParamAnnotation(),
        'sortDirection': ParamAnnotation(required=False, valid_values=['asc', 'desc'], non_empty=False,
                                         null_elements=False, empty_string=True, no_trim=False),
        'fields': ParamAnnotation(),
        'systemTags': ParamAnnotation(),
        'userTags': ParamAnnotation(),
    }

    def __init__(self):
        self.conditions = None
        self.limit = None
        self.start = None
        self.count = None
        self.groupBy = None
        self.replyWithCount = None
        self.sortBy = None
        self.sortDirection = None
        self.fields = None
        self.systemTags = None
        self.userTags = None
        super().__init__()


class CreateVmInstanceAction(AbstractAction):
    HTTP_METHOD = 'POST'
    PATH = '/vm-instances'
    NEED_SESSION = True
    NEED_POLL = True
    PARAM_NAME = 'params'

    PARAMS = {
        'name': ParamAnnotation(required=True, max_length=255, non_empty=False, null_elements=False, empty_string=True,
                                no_trim=False),
        'instanceOfferingUuid': ParamAnnotation(required=True, non_empty=False, null_elements=False, empty_string=True,
                                                no_trim=False),
        'imageUuid': ParamAnnotation(required=True, non_empty=False, null_elements=False, empty_string=True,
                                     no_trim=False),
        'l3NetworkUuids': ParamAnnotation(required=True, non_empty=True, null_elements=False, empty_string=True,
                                          no_trim=False),
        'type': ParamAnnotation(required=False, valid_values=['UserVm', 'ApplianceVm'], non_empty=False,
                                null_elements=False, empty_string=True, no_trim=False),
        'rootDiskOfferingUuid': ParamAnnotation(required=False, non_empty=False, null_elements=False, empty_string=True,
                                                no_trim=False),
        'dataDiskOfferingUuids': ParamAnnotation(required=False, non_empty=False, null_elements=False,
                                                 empty_string=True, no_trim=False),
        'zoneUuid': ParamAnnotation(required=False, non_empty=False, null_elements=False, empty_string=True,
                                    no_trim=False),
        'clusterUuid': ParamAnnotation(required=False, non_empty=False, null_elements=False, empty_string=True,
                                       no_trim=False),
        'hostUuid': ParamAnnotation(required=False, non_empty=False, null_elements=False, empty_string=True,
                                    no_trim=False),
        'primaryStorageUuidForRootVolume': ParamAnnotation(required=False, non_empty=False, null_elements=False,
                                                           empty_string=True, no_trim=False),
        'description': ParamAnnotation(required=False, max_length=2048, non_empty=False, null_elements=False,
                                       empty_string=True, no_trim=False),
        'defaultL3NetworkUuid': ParamAnnotation(),
        'strategy': ParamAnnotation(required=False, valid_values=['InstantStart', 'JustCreate'], non_empty=False,
                                    null_elements=False, empty_string=True, no_trim=False),
        'resourceUuid': ParamAnnotation(),
        'systemTags': ParamAnnotation(),
        'userTags': ParamAnnotation(),
    }

    def __init__(
            self,
            name=None,
            instance_offering_uuid=None,
            image_uuid=None,
            l3_network_uuids=None,
            type=None,
            rootDiskOfferingUuid=None,
            dataDiskOfferingUuids=None,
            zoneUuid=None,
            clusterUuid=None,
            hostUuid=None,
            primaryStorageUuidForRootVolume=None,
            description=None,
            defaultL3NetworkUuid=None,
            strategy=None,
            resourceUuid=None,
            systemTags=None,
            userTags=None,
    ):
        self.name = name
        self.instanceOfferingUuid = instance_offering_uuid
        self.imageUuid = image_uuid
        self.l3NetworkUuids = l3_network_uuids
        self.type = type
        self.rootDiskOfferingUuid = rootDiskOfferingUuid
        self.dataDiskOfferingUuids = dataDiskOfferingUuids
        self.zoneUuid = zoneUuid
        self.clusterUuid = clusterUuid
        self.hostUuid = hostUuid
        self.primaryStorageUuidForRootVolume = primaryStorageUuidForRootVolume
        self.description = description
        self.defaultL3NetworkUuid = defaultL3NetworkUuid
        self.strategy = strategy
        self.resourceUuid = resourceUuid
        self.systemTags = systemTags
        self.userTags = userTags
        super().__init__()
