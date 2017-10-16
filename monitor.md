# 监控系统

# 2014 zabbix

JMX 监控 jmx-gateway

使用脚本满足不同系统定制化监控指标

MySQL agent userparameter
```
UserParameter=mysql.status[*],echo "show global status where Variable_name='$1';" | HOME=/etc/zabbix /usr/local/mysql/bin/mysql -N | awk '{print $$2}'

# Flexible parameter to determine database or table size. On the frontend side, use keys like mysql.size[zabbix,history,data].
# Key syntax is mysql.size[<database>,<table>,<type>].
# Database may be a database name or "all". Default is "all".
# Table may be a table name or "all". Default is "all".
# Type may be "data", "index", "free" or "both". Both is a sum of data and index. Default is "both".
# Database is mandatory if a table is specified. Type may be specified always.
# Returns value in bytes.
# 'sum' on data_length or index_length alone needed when we are getting this information for whole database instead of a single table
UserParameter=mysql.size[*],echo "select sum($(case "$3" in both|"") echo "data_length+index_length";; data|index) echo "$3_length";; free) echo "data_free";; esac)) from information_schema.tables$([[ "$1" = "all" || ! "$1" ]] || echo " where table_schema='$1'")$([[ "$2" = "all" || ! "$2" ]] || echo "and table_name='$2'");" | HOME=/etc/zabbix /usr/local/mysql/bin/mysql -N

UserParameter=mysql.ping,HOME=/etc/zabbix /usr/local/mysql/bin/mysqladmin ping | grep -c alive
UserParameter=mysql.version,/usr/local/mysql/bin/mysql -V
UserParameter=mysql.threads,HOME=/etc/zabbix /usr/local/mysql/bin/mysqladmin status|cut -f3 -d":"|cut -f1 -d"Q"
UserParameter=mysql.qps,HOME=/etc/zabbix /usr/local/mysql/bin/mysqladmin status|cut -f9 -d":"
...
```

# problem
* 插件难开发， 定制化难度大
* 运行2年，大量数据查询缓慢 - Tokudb 引擎适合查询，不适合写入，清理过期数据

# 2016 open-falcon

why?
* 采集 收集 存储 分发 报警 分离组件部署方式 vs 单一部署
* Graph 底层采用 rrdtool 作为 metric 的存储，其特点单个指标存储空间固定，适合监控热数据的存储
* 高性能 Graph 应用层对 rrdtool 做了写优化 (缓存，分批磁盘写等)，单节点Graph 支持 8w +/秒数据点写入频率
* Transfer Graph 组件支持集群， 一致性hash分片

Transfer + Graph + Query 的组合构成了可横向扩展，技术门槛低，分布式时间序列化数据存储系统。


监控指标定制化插件开发 https://github.com/nxintech/open-falcon-plugins

# prometheus

特点
* 灵活的搜索语言 PromQl， falcon query 语法简陋，没有维度
* 通过基于HTTP的 pull 方式采集时序数据，开发简单
* 生态系统

定制化
* PMM
* alertmanger 报警整合 slack


# 后续
falcon-plus Open-Falcon v0.2

前端整合
* Open-Falcon 所有前端组件进行了统一整合
* Dashboard 全站增加权限控制，增加删除指定 endpoint、counter 以及对应的 rrd 文件的功能
* Dashboard 首页默认展示 endpoint 列表，并支持 endpoint 列表和 counter 列表翻页功能；
* Dashboard 增加删除一级 screen 的功能
* Dashboard 支持展示过往的历史报警信息
* 支持将报警的 callback 参数和内容在 Dashboard 页面上展示；
* 支持微信报警通道；


后端整合
* alarm支持报警历史信息入库存储和展示；
* 「报警合并」模块links的功能合并到统一前端 Dashboard 中，降低用户配置和维护成本；
* 「报警发送」模块sender的功能合并到 alarm 中，降低用户配置和维护成本；
* query的功能合并到了falcon-api组件中；
* 支持非周期性上报数据存储；
* agent支持通过自定义配置，只采集指定磁盘挂载点的磁盘监控数据；
* agent支持配置一个默认 tag，这样通过该 agent 上报的所有数据都会自动追加这个tag；
* judge新增报警判断函数lookup(#num, limit)，如果检测到过去num个周期内，有limit次符合条件就报警；

RESTful API

alcon-plus 所有的功能都可以通过 RESTful API 来完成


prometheus 高可用

报警方式多样化， 短信、微信、邮件、slack