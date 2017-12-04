# -*- coding:utf-8 -*-
from ldap3 import Server, Connection

server = Server(host='ldap://10.211.254.49', port=10389)
conn = Connection(server, user='uid=admin,ou=system', password='secret',
                  auto_bind=True, read_only=True, auto_referrals=False)

# Setting ldap.OPT_REFERRALS to 0 tells the server not to "chase" referrals, i.e. not to resolve them
print(server.info)

# bind
# dn = "uid=admin,ou=system"
# pw = "secret"
# conn = ldap.initialize("ldap://10.211.254.49:10389")
# conn.simple_bind_s(dn, pw)
#
# conn.set_option(ldap.OPT_REFERRALS, 0)
# conn.protocol_version = ldap.VERSION3
#
# for entry in conn.search_s(
#         'uid=liuyangc3,ou=developer,dc=nxin,dc=com',
#         scope=ldap.SCOPE_SUBTREE):
#     print(entry)
