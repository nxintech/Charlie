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

# Ansible dynamic inventory
ansible dynamic inventory via aliyun

set `access_key` `access_key_secret` and `region_id` in inventory.py
 and `pip install aliyun-python-sdk-ecs`
 
require `git` command installed

查询的主机信息保存到缓存文件(失效时间24小时)，不必每次去API查询


根据主机名查询主机信息
```
python inventory.py --host hostname
```
强制刷新缓存
```
python inventory.py --refresh 
```
列出所有主机
```
python inventory.py --list
```

--list 支持过滤 ECS InstanceAttributesType, 注意此功能并非给 ansible dynamic inventory 使用，
仅仅为了方便查找主机
```
# expression for ECS InstanceAttributes
python inventory.py --list -e OSType=windows
python inventory.py --list -e Status=Running

# expression for regx match
python inventory.py --list -e OSType=lin
python inventory.py --list -e InstanceTypeFamily=ecs.sn2
python inventory.py --list -e PrivateIpAddress=10.112.17

# tags
python inventory.py --list --tag service=tomcat
python inventory.py --list --tag project=农信金融
```

主机按照 ECS `tag value` 分组，例如 ECS 的`Tags: [{key: "project", value: "农信金融"}, {key: "service", value: "tomcat"}]`
```
ansible 农信金融 -i inventory.py -m ping
ansible tomcat -i inventory.py -m ping
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
