# SDK
Python SDK install
```
pip install aliyun-python-sdk-core
pip install aliyun-python-sdk-ecs
pip install aliyun-python-sdk-vpc
pip install aliyun-python-sdk-ros
```

buf fix https://github.com/aliyun/aliyun-openapi-python-sdk/issues/22

# Doc
ALIYUN::ECS::Instance

https://help.aliyun.com/document_detail/28871.html?spm=5176.doc48893.2.9.PR37Bn

# Client
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
    instance_type="ecs.sn2.medium",  # 2C4G
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


# API
ECS

https://help.aliyun.com/document_detail/25485.html?spm=5176.doc25469.6.786.paKdQW


DescribeZones

https://help.aliyun.com/document_detail/25610.html?spm=5176.doc25485.2.72.KgxL9O

ZoneType

https://help.aliyun.com/document_detail/25640.html?spm=5176.doc25610.2.2.AIaWsG