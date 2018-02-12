# nx-proj client
dependences

```console
pip install requests
# 2.7 +
pip install enum35 future
```

example
```python
from client import *
c = Client(username='admin', password='')

# all projects
for p in c.get_projects():
    print(p.name)

# get project info
zntapi = c.get_project('zntapi')
print(zntapi.name)

# get build package url
url = c.get_project_package('zntapi')


# add project
project = Project(
    "test-project", "this is a test project",
    BuildInfo('http://git.example.com', RepoType.git),
    hostnames=["xx.1", "xx.2"])

c.add_project(project)
```