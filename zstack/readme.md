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


`zssdk3.py` py3 全新异步 sdk，兼容老 sdk Action，调用方式
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
