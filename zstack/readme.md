# ansible dynamic inventory
need python3.5 +

`zssdk.py` 官方 python SDK，并在其基础上做了一些修改用于适配 py3

`inventory.py` ansible dynamic inventory, 自动生成 .cache 文件，
记录 hostname 和 VmInstance uuid 的映射关系。
```
python inventory.py --list
python inventory.py --host xx.teat.zs 

# 显示 API 的 请求和响应
python inventory.py --list --debug
```


`zssdk3.py` py3 全新异步 sdk，兼容老 sdk Action

依赖
```
# python3.5+
pip install ujson
pip install uvloop
pip install aiohttp
```

使用方式
```
# 配置 action
action = SomeAction()
action.xxx = xxx
...

loop = asyncio.get_event_loop()
client = ZStackClient(host="zstack.nxin.com", loop=loop)
client.set_session("account", "username", "password")
r = loop.run_until_complete(client.request_action(q))
print(r)
```

`inventory3.py` 根据 py3 SDK 实现的 ansible dynamic inventory

```
python inventory3.py --host 网络测试陪练机4
{
  "ansible_ssh_user":"root",
  "ansible_ssh_host":"10.xxx.xxx.xxx",
  "ansible_ssh_port":22,
  "zstack":{
    "uuid":"26731bf3b6944b8e98a95500f42b4781",
    "name":"\u7f51\u7edc\u6d4b\u8bd5\u966a\u7ec3\u673a4",
    "description":"",
    "zoneUuid":"053407e87ae74f98948dbfa637342c31",
    "clusterUuid":"6675568827b744b2a592d192ee2a58d6",
    "imageUuid":"e5cbff6ca9885a4395cf984773b2018e",
    "hostUuid":"9dcd974f612b43dfbccba37e15fb422a",
    "lastHostUuid":"d91a2c0070604e05a0faf6a5fab32b7c",
    "instanceOfferingUuid":"34d32c5368324a2b9d7d82f7b9167d87",
    "rootVolumeUuid":"812e952e81bb4ceeb5b76a3ce7f1cbe0",
    "platform":"Linux",
    "defaultL3NetworkUuid":"420e6c0e6b0d4819ac5c277a0a1b2db5",
    "type":"UserVm",
    "hypervisorType":"KVM",
    "memorySize":8589934592,
    "cpuNum":4,
    "cpuSpeed":0,
    "allocatorStrategy":"LeastVmPreferredHostAllocatorStrategy",
    "createDate":"Nov 22, 2017 10:56:32 AM",
    "lastOpDate":"Nov 22, 2017 3:43:24 PM",
    "state":"Running",
    "internalId":135,
    "vmNics":[
      {
        "uuid":"e9d1dd78dd9049339ff70c2edf2119bf",
        ...
        "createDate":"Nov 22, 2017 10:56:32 AM",
        "lastOpDate":"Nov 22, 2017 10:56:32 AM"
      }
    ],
    "allVolumes":[
      {
        "uuid":"812e952e81bb4ceeb5b76a3ce7f1cbe0",
        "name":"ROOT-for-\u7f51\u7edc\u6d4b\u8bd5\u966a\u7ec3\u673a4",
        "description":"Root volume for VM[uuid:26731bf3b6944b8e98a95500f42b4781]",
        ...
        "state":"Enabled",
        "status":"Ready",
        "createDate":"Nov 22, 2017 10:56:32 AM",
        "lastOpDate":"Nov 22, 2017 10:56:33 AM",
        "isShareable":false
      }
    ]
  }
```