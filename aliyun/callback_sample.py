from metad.metad import Client


data = {'instance_id': '0aa80347-f7bd-49e7-b495-8ba06cb77e9c',
 'os_username': 'root',
'os_password': 'ustack',
 'mac': 'fa:16:3e:b2:ad:c4',
 'address': '10.211.253.223',
 'hostname': 'liutest3.yz',
 'project_id': '5eabd31c9803431cbb8e6f2c59df0683',
 }

def callback(result, config):
    config
    client = Client(host="")
    endpoint = "/nodes/{}".format(instance_id)
    res = client.mput(endpoint, data)