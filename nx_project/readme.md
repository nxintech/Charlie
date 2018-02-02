# nx-proj client
example
```python
from client import Client
c = Client(username='admin', password='')

# all projects
for p in c.get_projects():
    print(p.name)

# get project info
zntapi = c.get_project('zntapi')
print(zntapi.name)

# get build package url
url = c.get_project_package('zntapi')
```