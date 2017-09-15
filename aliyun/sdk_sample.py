import json
import pprint

from aliyunsdkcore.client import AcsClient
from aliyunsdkros.request.v20150901 import \
    DescribeRegionsRequest
from aliyunsdkvpc.request.v20160428 import \
    DescribeVSwitchesRequest
from aliyunsdkecs.request.v20140526 import \
    DescribeZonesRequest, \
    DescribeImagesRequest, \
    DescribeInstanceTypesRequest, \
    DescribeSecurityGroupsRequest, \
    DescribeSecurityGroupAttributeRequest

pp = pprint.PrettyPrinter(indent=2)

access_key = ''
access_key_secret = ''
client = AcsClient(access_key, access_key_secret, 'cn-beijing')

# print Regions
req = DescribeRegionsRequest.DescribeRegionsRequest()
body = client.do_action_with_exception(req)
pp.pprint(json.loads(body.decode("utf-8")))

# VSwitch
req = DescribeVSwitchesRequest.DescribeVSwitchesRequest()
req.set_query_params({'PageSize': 50})
body = client.do_action_with_exception(req)
pp.pprint(json.loads(body.decode("utf-8")))

# zone
req = DescribeZonesRequest.DescribeZonesRequest()
body = client.do_action_with_exception(req)
pp.pprint(json.loads(body.decode("utf-8")))

# SecurityGroup
req = DescribeSecurityGroupsRequest.DescribeSecurityGroupsRequest()
req.set_query_params({'PageSize': 50})
body = client.do_action_with_exception(req)
pp.pprint(json.loads(body.decode("utf-8")))

# SecurityGroup id
req = DescribeSecurityGroupAttributeRequest.DescribeSecurityGroupAttributeRequest()
req.set_SecurityGroupId("")
body = client.do_action_with_exception(req)
pp.pprint(json.loads(body.decode("utf-8")))

# InstanceType
req = DescribeInstanceTypesRequest.DescribeInstanceTypesRequest()
req.set_query_params({'PageSize': 50})
body = client.do_action_with_exception(req)
pp.pprint(json.loads(body.decode("utf-8")))

# ImageId
req = DescribeImagesRequest.DescribeImagesRequest()
req.set_query_params({'PageSize': 10})
req.set_query_params({'ImageId': ""})
body = client.do_action_with_exception(req)
pp.pprint(json.loads(body.decode("utf-8")))
