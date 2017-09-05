import json
import pprint
from jinja2 import Environment, FileSystemLoader

from aliyunsdkcore.client import AcsClient
from aliyunsdkros.request.v20150901 import DescribeRegionsRequest

pp = pprint.PrettyPrinter(indent=4)

env = Environment(loader=FileSystemLoader('template'))
template = env.get_template('tomcat.j2')
instance_types = ["ecs.s2.medium", "ecs.s2.large", "ecs.s3.medium", "ecs.s3.large"]
stack = template.render(
    image_id='',
    instance_types=instance_types,
    resource_name='fuck')
print(stack)

access_key = ''
access_key_secret = ''
client = AcsClient(access_key, access_key_secret, 'cn-beijing')

# print Regions
req = DescribeRegionsRequest.DescribeRegionsRequest()
body = client.do_action_with_exception(req)
pp.pprint(json.loads(body.decode("utf-8")))