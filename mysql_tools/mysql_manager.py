# -*- coding:utf-8 -*-


class Grant(object):
    def __init__(self, privilege, database, table, user, host, password):
        """
        :param privilege: 权限列表 或 权限
        :type privilege: list or str
        :param database: database name
        :param table: table name
        :param user: username
        :param host: host
        """
        if isinstance(privilege, (list, tuple)):
            self.privilege = privilege
        else:
            self.privilege = [privilege]
        self.database = database
        self.table = table
        self.user = user
        self.host = host
        self.password = password

    def __repr__(self):

        return "GRANT {0} ON {1}.{2} TO {3}@'{4}' IDENTIFIED BY '{5}';".format(
            ",".join(self.privilege), self.database, self.table, self.user, self.host, self.password)


class FuncGrant(Grant):
    def __init__(self, privilege, database, table, user, host, password):
        super(FuncGrant, self).__init__(privilege, database, table, user, host, password)

    def __repr__(self):
        return "GRANT FUNCTION {0} ON {1}.{2} TO {3}@'{4}' IDENTIFIED BY '{5}';".format(
            ",".join(self.privilege), self.database, self.table, self.user, self.host, self.password)


class Instance(object):
    PRIVILEGES = ["ALL", "TRIGGER", "EXECUTE", "DROP", "SELECT", "INSERT", "UPDATE", "DELETE", "REPLICATION SLAVE",
                  "REPLICATION CLIENT"]
    ROLES = ['master', 'slave']

    def __init__(self, host, port, version, database=None, role=None):
        """
        :param host: 实例 host
        :param port: 实例 端口
        :param version: 数据库版本

        role:   角色 master/slave
        grants: 授权对象列表
        """
        self.host = host
        self.port = port
        self.version = version
        self.databases = ['mysql', 'information_schema', 'performance_schema']
        if database:
            if isinstance(database, (str, unicode)):
                self.add_database(database)
            if isinstance(database, (list, tuple)):
                for db in database:
                    self.add_database(db)
        if role:
            if role not in self.ROLES:
                raise ValueError("role {0} not in {1}".format(role, self.ROLES))
            self.role = role
        else:
            self.role = None
        self.grants = []

    def add_database(self, database):
        database = database.lower()
        if self.database_exist(database):
            raise TypeError('database {0} already in {1}'.format(database, self.databases))
        else:
            self.databases.append(database)

    def database_exist(self, database):
        return database in self.databases

    def grant(self, privilege, database, table, user, host, password):
        """
        :param privilege: 权限
        :param database: 数据库名
        :param table: 表名
        :param user: 用户名
        :param host: 主机地址
        :param password: 密码
        """
        if self.role != 'master':
            raise TypeError('should do a grant on a master instance')

        database = database.lower()
        if not self.database_exist(database):
            raise TypeError('database {0} not in databases: {1}'.format(database, self.databases))

        if isinstance(privilege, str) or isinstance(privilege, unicode):
            privilege = privilege.upper()
            if privilege not in self.PRIVILEGES:
                raise TypeError('privilege {0} not in {1}'.format(privilege, self.PRIVILEGES))
        if isinstance(privilege, list) or isinstance(privilege, tuple):
            privilege = [p.upper() for p in privilege]
            if not set(privilege).issubset(set(self.PRIVILEGES)):
                raise TypeError('privileges {0} not in {1}'.format(privilege, self.PRIVILEGES))

        if privilege == 'EXECUTE':
            grant = FuncGrant(privilege, database, table, user, host, password)
        else:
            grant = Grant(privilege, database, table, user, host, password)

        if self.grant_exist(grant):
            raise ValueError("grant [{0}] already exist".format(grant))
        else:
            self.grants.append(grant)

    def grant_exist(self, grant):
        grant_str = str(grant)
        return any(str(g) == grant_str for g in self.grants)


class Database(object):
    def __init__(self, name):
        self.name = name
        self.tables = []

    def append(self, table):
        if table not in self.tables:
            self.tables.append(table)
        else:
            raise ValueError("'{0}' already in database".format(table))
