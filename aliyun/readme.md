# SDK
Python SDK install
```
# py2
pip install aliyun-python-sdk-core
# py3
pip install aliyun-python-sdk-core-v3
pip install aliyun-python-sdk-ecs
pip install aliyun-python-sdk-vpc
pip install aliyun-python-sdk-ros
```
you need fix bug before run code, see https://github.com/aliyun/aliyun-openapi-python-sdk/issues/22

# Client
ues Python > 3.5

```python
from aliyun.client import Instance, Aliyun

ali = Aliyun("access_key", "access_value", region="cn-beijing")
instance = Instance(ali.client)
instance.new_instance(
    zone="cn-beijing-a",
    vswitch="VSwitchId",
    security_group="SecurityGroupId",
    image="ImageId",
    instance_name=None,
    hostname="te-st.produce.yz",
    password="Xxx",
    private_ip_address=None,
    instance_type="ecs.sn2.medium",  # 2c8g ecs.sn2.medium | 4c8g ecs.sn1.large
    instance_charge_type="PrePaid",
    period=1,
    internet_charge_type="PayByTraffic",
    io_optimized="optimized",
    userdata=None,
)

instance.add_disk("cloud_efficiency", 40, disk_type="system")
instance.add_disk("cloud_efficiency", 100, disk_type="data")
instance.add_tag("project_id", "test")
res = ali.create_instance(instance)

print(res)
```

# ROS
```python
import json
from jinja2 import Environment, FileSystemLoader
from aliyunsdkcore.client import AcsClient
from aliyunsdkros.request.v20150901 import CreateStacksRequest

env = Environment(loader=FileSystemLoader('template'))

template = env.get_template('tomcat.j2')
stack = template.render(
    resource_name='tomcat7',
    image_id="",
    password="",
    hostname="test.nxin.ali",
    private_ip_addr='10.112.254.1',
    project_id='ceshi',
    zone_id='cn-beijing-a',
    vpc_id="",
    vswitch_id="",
    security_group_id="",
    period=1)
    
# create stack
client = AcsClient("access_key", "access_key_secret", 'cn-beijing')
req = CreateStacksRequest.CreateStacksRequest()
req.set_headers({'x-acs-region-id': 'cn-beijing'})
req.set_content('{"Name": "create_ecs_tomcat","TimeoutMins": 60,"Template": %s}' % stack)
body = client.do_action_with_exception(req)
print(json.loads(body.decode("utf-8")))
```

# API
ECS

https://help.aliyun.com/document_detail/25485.html?spm=5176.doc25469.6.786.paKdQW

ALIYUN::ECS::Instance

https://help.aliyun.com/document_detail/28871.html?spm=5176.doc48893.2.9.PR37Bn

DescribeZones

https://help.aliyun.com/document_detail/25610.html?spm=5176.doc25485.2.72.KgxL9O

ZoneType

https://help.aliyun.com/document_detail/25640.html?spm=5176.doc25610.2.2.AIaWsG

# Ansible
set `access_key` `access_key_secret` and `region_id` before run ansible-inventory.py
```
pip install aliyun-python-sdk-ecs
wget https://raw.githubusercontent.com/nxintech/Charlie/master/aliyun/ansible-inventory.py
python ansible-inventory.py --list
```