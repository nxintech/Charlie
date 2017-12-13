# Zstack sdk
need python3.5 +

`zssdk.py` 官方 python SDK，并在其基础上做了一些修改用于适配 py3

`zssdk3.py` py3 全新异步 sdk，兼容老 sdk Action， 推荐使用 zssdk3.py


创建VM
```python
import asyncio
from zssdk3 import CreateVmInstanceAction, ZStackClient

# 全局初始化代码
loop = asyncio.get_event_loop()
client = ZStackClient(host="zstack.nxin.com", loop=loop)
client.set_session("account", "username", "password")

# create vm
q = CreateVmInstanceAction(
    name='test-create-vm.sz',
    description='create by python sdk3',
    instance_offering_uuid='2fb29451e02c4435a374289092cd5dcc',  # 1c1g
    image_uuid='ae0ac51648a6424e95714575730510a1',  # centos 7
    l3_network_uuids=['l3net_id'],
    strategy='InstantStart',
    systemTags=["staticIp::l3net_id::your_ip"])
resp = loop.run_until_complete(client.request_action(q))
print(resp)
```

批量创建
```python
tasks = []

q1 = CreateVmInstanceAction(...)
tasks.append(client.request_action(q1))

q2 = CreateVmInstanceAction(...)
tasks.append(client.request_action(q2))

q3 = CreateVmInstanceAction(...)
tasks.append(client.request_action(q3))

results = loop.run_until_complete(asyncio.gather(*tasks))
for resp in results:
    print(resp)
```

查询 VM
```python
from zssdk3 import QueryOneVmInstance, QueryVmInstanceAction

# query one Vm with uuid
q = QueryOneVmInstance()
q.uuid = "your vm_uuid"
resp = loop.run_until_complete(client.request_action(q))
print(resp)

# query all Vms
q = QueryVmInstanceAction()
q.conditions = ["type=UserVm"]
q.replyWithCount = True
q.limit = 100
q.start = 0

total = 0
count = 0
while q.start == 0 or count < total:
    resp = loop.run_until_complete(client.request_action(q))
    print(resp)
    
    total = resp["value"]["total"]
    count += len(resp["value"]["inventories"])
    q.start += q.limit
    
    
# query Vms with a tag
q = QueryVmInstanceAction()
q.conditions = ["type=UserVm", "__userTag__=app::tomcat::7.0.70"]
q.fields = ["name"]
resp = loop.run_until_complete(client.request_action(q))
for i in resp['value']['inventories']:
    print(i)
```

# ansible dynamic inventory 

`inventory.py` 适用于 Python2.7+ 环境

`inventory3.py` 根据 py3 SDK `zssdk3.py` 实现的 ansible dynamic inventory

依赖
```
# python3.5+
pip install ujson
pip install uvloop
pip install aiohttp
```

列出所有主机信息
```
python inventory3.py --list

{
  "_meta":{
    "hostvars":{
      "nx-xxxx.produce.zs":{
        "ansible_ssh_user":"root",
        "ansible_ssh_host":"10.xx.xx.xx",
        "ansible_ssh_port":22,
        "zstack":{
          "uuid":"------------------",
          "name":"nx-xxxx.produce.zs",
...
```

指定主机名查看 VM 信息 `python inventory3.py --host <vm hostname>`
```
python inventory3.py --host 网络测试陪练机4
{
  "ansible_ssh_user":"root",
  "ansible_ssh_host":"10.xxx.xxx.xxx",
  "ansible_ssh_port":22,
  "zstack":{
    "uuid":"----------------",
    "name":"\u7f51\u7edc\u6d4b\u8bd5\u966a\u7ec3\u673a4",
    "description":"",
    ...
  }
```

列出可用的主机组
```
python inventory3.py --app
dict_keys(['tomcat', 'rabbitmq', 'svn', 'ansible', 'gitlab', 'elasticsearch', 'nexus', 
'others', 'kafka', 'bind', 'haproxy', 'etcd', 'dns', 'ldap', 'openresty', 'zookeeper',
'falcon', 'memcache', 'pmm-server', 'template', 'jumpserver', 'memcacheq', 'jenkins', 'prometheus'])

# use host group
ansible tomcat -m ping
```

显示特定主机组
```
python inventory3.py  --show zookeeper
['zookeeper02.produce.zs', 'zookeeper03.produce.zs', 'zookeeper01.produce.zs']
```

查看 hostname 和 VmInstance uuid 的映射关系
```
python inventory3.py  --map
{   'xx01.produce.zs': 'c017**************************27',
    'xx02.produce.zs': 'a57a**************************18',
```

debug
```
# notice: this only works on sdk `zssdk.py` and `inventory.py`
python inventory.py --list --debug # 显示 zssdk.py 调用 API： 请求和响应
```