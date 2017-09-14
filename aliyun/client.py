import re
import json
import base64
import ipaddress


from aliyunsdkcore.client import AcsClient
from aliyunsdkvpc.request.v20160428 import \
    DescribeVSwitchAttributesRequest
from aliyunsdkecs.request.v20140526 import \
    DescribeZonesRequest, \
    CreateInstanceRequest, \
    DescribeImagesRequest, \
    DescribeSecurityGroupAttributeRequest


class Tag(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value


class Disk(object):
    """
    :param category: DiskCategory: "cloud"|"cloud_efficiency"|"cloud_ssd"|"ephemeral_ssd".
    :param size: DiskSize GB, 40~500.
    """

    def __init__(self, category, size):
        self.__category = None
        self.__size = None
        self.category = category
        self.size = size

    @property
    def category(self):
        return self.__category

    @category.setter
    def category(self, category):
        supported = ["cloud", "cloud_efficiency", "cloud_ssd", "ephemeral_ssd"]
        if category not in supported:
            raise ValueError("category should be one of [%s]" % ",".join(supported))
        self.__category = category

    @property
    def size(self):
        return self.__size

    @size.setter
    def size(self, size):
        if 500 < size or size < 40:
            raise ValueError("Disk size should between 40~500.")
        self.__size = size


def config(param, not_none=False, depend=None):
    def decorator(func):
        def wrapper(self, value):
            if not_none and value is None:
                raise ValueError("Param \"%s\" can not be None." % param)
            if depend and depend not in self.config:
                raise ValueError("Param \"%s\" depend on \"%s\" witch is not set." % (param, depend))
            if value is None:
                return
            self.config[param] = func(self, value)

        return wrapper

    return decorator


class Config(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


class Instance(object):
    def __init__(self, client):
        """
        :param AcsClient client: class AcsClient
        """
        self.client = client
        self.system_disk = None
        self.data_disks = []
        self.tags = []
        self.config = Config()

    def new_instance(self,
                     zone=None,
                     vswitch=None,
                     security_group=None,
                     image=None,
                     instance_name=None,
                     hostname=None,
                     password=None,
                     private_ip_address=None,
                     instance_type="ecs.sn2.medium",
                     instance_charge_type=None,
                     internet_charge_type=None,
                     period=None,
                     io_optimized="optimized",
                     userdata=None
                     ):
        """Create a Instance
        
        :param zone: ZoneI.
        :param vswitch: VSwitchId.
        :param security_group: dictionary of headers to send.
        :param image: ImageId.
        :param instance_name: InstanceName.
        :param hostname: the body to attach to the request. If a dictionary is provided, form-encoding will take place.
        :param password: json for the body to attach to the request (if files or data is not specified).
        :param private_ip_address: private ip address, vpc only.
        :param internet_charge_type: "PayByTraffic" or "PayByBandwidth", not used in VPC.
        :param instance_type: 2C8G "ecs.sn2.medium", 4C8G "ecs.sn1.large".
        :param instance_charge_type: "PrePaid" or "PostPaid".
        :param period: pay months, only works when instance_charge_type is "PrePaid".
        :param io_optimized: "optimized" | "none".
        :param userdata: init script when instance created, value must be encoded by ase64.
        """

        self.zone(zone)
        self.vswitch(vswitch)
        self.security_group(security_group)
        self.image(image)
        self.instance_name(instance_name)
        self.hostname(hostname)
        self.password(password)
        self.private_ip_address(private_ip_address)
        self.instance_type(instance_type)
        self.internet_charge_type(internet_charge_type)
        self.instance_charge_type(instance_charge_type)
        self.period(period)
        self.io_optimized(io_optimized)
        self.userdata(userdata)

    @config("ZoneId", not_none=True)
    def zone(self, zone_id):
        return zone_id

    @config("VSwitchId", not_none=True)
    def vswitch(self, vswitch_id):
        vsw = self.__request_vswitch(vswitch_id)
        if vsw['VSwitchId'] == "":
            raise ValueError("VSwitchId \"%s\" not find" % vswitch_id)
        return vswitch_id

    def __request_vswitch(self, vswitch_id):
        req = DescribeVSwitchAttributesRequest.DescribeVSwitchAttributesRequest()
        req.set_VSwitchId(vswitch_id)
        body = self.client.do_action_with_exception(req)
        return json.loads(body.decode("utf-8"))

    @config("SecurityGroupId", not_none=True)
    def security_group(self, security_group_id):
        self.__request_security_group(security_group_id)
        return security_group_id

    def __request_security_group(self, security_group_id):
        # if SecurityGroupId not found, server will return 404 and sdk
        # will raise A aliyunsdkcore.acs_exception.exceptions.ServerException
        # this behaviour is not same as DescribeVSwitchAttributesRequest
        # which just return a empty response, so we don't need raise
        # any exceptions here.
        req = DescribeSecurityGroupAttributeRequest.DescribeSecurityGroupAttributeRequest()
        req.set_SecurityGroupId(security_group_id)
        body = self.client.do_action_with_exception(req)
        return json.loads(body.decode("utf-8"))

    @config("ImageId", not_none=True)
    def image(self, image_id):
        self.__request_image(image_id)
        return image_id

    def __request_image(self, image_id):
        req = DescribeImagesRequest.DescribeImagesRequest()
        req.set_query_params({'PageSize': 50})
        req.set_query_params({'ImageId': "image_id"})
        body = self.client.do_action_with_exception(req)
        res = json.loads(body.decode("utf-8"))
        if res['TotalCount'] == 0:
            raise ValueError("ImageId <%s> not found" % image_id)

    @config("HostName", not_none=True)
    def hostname(self, name):
        if len(name) < 2 or len(name) > 30:
            raise ValueError("HostName length should between 2~30.")
        parts = name.split('.')
        if len(parts) < 3:
            raise ValueError("HostName at least has 3 part")
        if parts[-1] != "ali" and (parts[-2] != "produce" or parts[-2] != "manage"):
            raise ValueError("HostName format not match \"*.produce.ali\" or \"*.manage.ali.\"")
        if not re.match('^[a-z][a-z0-9-]*$', parts[0]):
            raise ValueError("HostName \"%s\" not match [a-z0-9] and '-'." % parts[0])
        return name

    @config("InstanceName")
    def instance_name(self, name):
        return name

    @config("Password", not_none=True)
    def password(self, p):
        if 30 < len(p) or len(p) < 8:
            raise ValueError("password length should between 8~30.")
        password_strong_check(p)
        return p

    @config("PrivateIpAddress", depend="VSwitchId")
    def private_ip_address(self, ip):
        self.check_private_ip_address(self.config["VSwitchId"], ip)

        return ip

    def check_private_ip_address(self, vswitch_id, ip):
        sg = self.__request_security_group(vswitch_id)
        network = sg['CidrBlock']
        if ipaddress.ip_address(ip) not in ipaddress.ip_network(network):
            raise ValueError("IP<%s> not match network <%s>" % (ip, network))

    @config("InstanceType", not_none=True)
    def instance_type(self, instance_type):
        check_instance_type(self.zone, self.is_io_optimized, instance_type)
        return instance_type

    @config("InternetChargeType", not_none=True)
    def internet_charge_type(self, charge_type):
        if charge_type not in ["PayByTraffic", "PayByBandwidth"]:
            raise ValueError("InternetChargeType valid value \"PayByTraffic\" or \"PayByBandwidth\"")
        return charge_type

    @config("InstanceChargeType", not_none=True)
    def instance_charge_type(self, charge_type):
        if charge_type not in ["PrePaid", "PostPaid"]:
            raise ValueError("InstanceChargeType valid value \"PrePaid\" or \"PostPaid\"")
        return charge_type

    @config("Period", depend="InstanceChargeType")
    def period(self, period):
        if period is None:
            return 1

        if self.config["InstanceChargeType"] != "PrePaid":
            raise ValueError("\"Period\" only works when Param \"InstanceChargeType\" is \"PrePaid\".")

        if 0 > period > 36:
            raise ValueError("Period should between 1~36.")

        return period

    @config("IoOptimized", not_none=True)
    def io_optimized(self, value):
        if value not in ["optimized", "none"]:
            raise ValueError("io_optimized valid value \"optimized\" or \"none\".")
        return value

    @property
    def is_io_optimized(self):
        return self.config["IoOptimized"] == "optimized"

    @config("UserData", not_none=True)
    def userdata(self, data):
        if not data:
            return
        return base64.b64encode(data.encode("utf-8"))

    def add_disk(self, category, size, disk_type="system"):
        if disk_type == "system":
            if self.system_disk:
                raise ValueError("already added system disk")
            self.__add_system_disk(category, size)

        if disk_type == "data":
            if len(self.data_disks) == 5:
                raise ValueError("Can't add more than 5 data disks")
            self.__add_data_disk(category, size)

    def __add_system_disk(self, category, size):
        # check_system_disk_categories(self.zone, self.is_io_optimized, category)
        self.system_disk = Disk(category, size)

    def __add_data_disk(self, category, size):

        self.data_disks.append(Disk(category, size))

    def add_tag(self, key, value):
        if len(self.tags) == 5:
            raise ValueError("Can't add more than 5 tags")
        self.tags.append(Tag(key, value))


class Aliyun(object):
    """
    :param access_key: access_key.
    :param access_secret: access_secret.
    :param region: region.
    """

    def __init__(self, access_key, access_secret, region="cn-beijing"):
        self.region = region
        self.client = AcsClient(access_key, access_secret, self.region)
        self.zones = None

    def request_page_query(self, req):
        page_size = 50
        index = 1
        req.set_query_params({'PageSize': page_size})
        req.set_query_params({'PageNumber', index})
        body = self.client.do_action_with_exception(req)
        res = json.loads(body.decode("utf-8"))
        total_count = res['TotalCount']
        if total_count <= page_size:
            yield res
        else:
            current_count = total_count
            while current_count < total_count:
                index += 1
                req.set_query_params({'PageNumber', index})
                body = self.client.do_action_with_exception(req)
                current_count += page_size
                yield json.loads(body.decode("utf-8"))

    def get_zone(self, zone_id):
        if not self.zones:
            self.zones = self.__request_zones()

        for zone in self.zones:
            if zone['ZoneId'] == zone_id:
                return zone

        raise ValueError("Invalid ZoneId.")

    def __request_zones(self):
        req = DescribeZonesRequest.DescribeZonesRequest()
        return self.__do_request(req)

    def __do_request(self, req):
        self.client.do_action_with_exception(req)
        body = self.client.do_action_with_exception(req)
        return json.loads(body.decode("utf-8"))

    def create_instance(self, instance, callback=None):
        """
        :param Instance instance: class Instance
        :param callback: callback function run after instance creation successfully.
        """
        c = instance.config
        zone = self.get_zone(c.ZoneId)
        check_resource_types(zone)
        check_instance_type(zone, instance.is_io_optimized, c.InstanceType)

        req = self.prepare_instance_create_request(zone, instance)
        res = self.__do_request(req)

        cb_res = None
        if callback:
            cb_res = self.handle_callback(callback, c)
        return res, cb_res

    def prepare_instance_create_request(self, zone, instance):
        c = instance.config
        request = CreateInstanceRequest.CreateInstanceRequest()
        request.set_accept_format('json')

        request.add_query_param('RegionId', self.region)
        for k, v in c.items():
            request.add_query_param(k, v)

        check_system_disk_categories(zone, instance.is_io_optimized, instance.system_disk)
        request.add_query_param('SystemDisk.Category', instance.system_disk.category)
        request.add_query_param('SystemDisk.Size', instance.system_disk.size)

        index = 1
        for disk in instance.data_disks:
            check_data_disk_categories(zone, instance.is_io_optimized, disk.category)
            request.add_query_param('DataDisk.%d.Category' % index, disk.category)
            request.add_query_param('DataDisk.%d.Size' % index, disk.size)
            index += 1

        index = 1
        for tag in instance.tags:
            request.add_query_param('Tag.%d.Key' % index, tag.key)
            request.add_query_param('Tag.%d.Value' % index, tag.value)
            index += 1

        return request

    def handle_callback(self, callback, *arg, **kwargs):
        return callback(arg, kwargs)


def check_resource_types(zone):
    zone_id = zone['ZoneId']
    local_name = zone['LocalName']
    supported = zone['AvailableResourceCreation']['ResourceTypes']
    if supported != ["VSwitch", "IoOptimized", "Instance", "Disk"]:
        raise ValueError("Zone<%s, %s> only support [%s]" % (
            zone_id, local_name, ",".join(supported)))


def check_system_disk_categories(zone, is_optimized, disk_category):
    zone_id = zone['ZoneId']

    for resource_info in zone['AvailableResources']['ResourcesInfo']:
        if resource_info['IoOptimized'] == is_optimized:
            supported = resource_info['SystemDiskCategories']['supportedSystemDiskCategory']
            if disk_category not in supported:
                raise ValueError("SystemDiskCategory <%s> not in [%s] in Zone<%s>" %
                                 (disk_category, ",".join(supported), zone_id))


def check_data_disk_categories(zone, is_optimized, disk_category):
    zone_id = zone['ZoneId']
    for resource_info in zone['AvailableResources']['ResourcesInfo']:
        if resource_info['IoOptimized'] == is_optimized:
            supported = resource_info['DataDiskCategories']['supportedDataDiskCategory']
            if disk_category not in supported:
                raise ValueError("DataDiskCategory <%s> not in [%s] in Zone<%s>" %
                                 (disk_category, ",".join(supported), zone_id))


def check_instance_type(zone, io_optimized, instance_type):
    zone_id = zone['ZoneId']
    for resource_info in zone['AvailableResources']['ResourcesInfo']:
        if resource_info['IoOptimized'] == io_optimized:
            supported = resource_info['InstanceTypes']['supportedInstanceType']
            if instance_type not in supported:
                raise ValueError("InstanceType <%s> not in [%s] in Zone<%s>" %
                                 (instance_type, ",".join(supported), zone_id))


def password_strong_check(p):
    number = re.compile(r'[0-9]')
    lower_case = re.compile(r'[a-z]')
    upper_case = re.compile(r'[A-Z]')
    others = re.compile(r'[`~!@#$%^&*\-+=|{}\[\]:;\'<>,\.?/]')

    if not number.search(p):
        raise ValueError("Password has no number")

    if not lower_case.search(p):
        raise ValueError("Password has no lower case")

    if not upper_case.search(p):
        raise ValueError("Password has no upper case")

    if not others.search(p):
        raise ValueError("Password has no special character")
