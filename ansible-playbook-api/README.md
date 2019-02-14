ansible 2.0 playbook api
-------------------------
running ansible playbook programmatically

使用
----
#### api
playbook_api.py 相同目录下新建 ansible.cfg 文件

human_log.py copy 到 ansible.cfg 中指定的 `callback_plugins` 路径

运行 playbook_api.py 


#### api new
```
hosts = 'localhost,192.168.0.1'

runner = Runner(hosts)
runner.set_module_path('/c/my_module')
runner.set_extra_vars({'key': 'value'})
rc, result = runner.run('pb.yml')
print(rc, result)
```

references
------------

https://docs.ansible.com/ansible/latest/dev_guide/developing_api.html

http://docs.ansible.com/ansible/intro_configuration.html#stdout-callback

https://serversforhackers.com/running-ansible-2-programmatically

https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/hipchat.py

https://gist.github.com/agaffney/0d026372aa0f1966f340
