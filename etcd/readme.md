### 安装
```
wget https://github.com/coreos/etcd/releases/download/v3.2.4/etcd-v3.2.4-linux-amd64.tar.gz
tar zxf etcd-v3.2.4-linux-amd64.tar.gz -C /opt/
mkdir /data0/etcd/{data,wal,logs} -p
```

### 启动
集群计划3台机器，还需要额外的etcd用于服务发现
```
# 服务发现机器的ip为 10.0.0.1
etcd --name `hostname` --initial-advertise-peer-urls http://0.0.0.0:2380 \
  --listen-peer-urls http://0.0.0.0:2380 \
  --listen-client-urls http://10.0.0.1:2379,http://127.0.0.1:2379 \
  --advertise-client-urls http://10.0.0.1:2379 \
  --data-dir /data0/etcd/data --wal-dir /data0/etcd/wal \
```
注册集群信息，台数为3
```
curl -XPUT http://10.0.0.1:2379/v2/keys/discovery/nxin/_config/size -d value=3
```
分别在每台机器上以集群方式启动
```
./etcd --name `hostname` --initial-advertise-peer-urls http://0.0.0.0:2380 \
  --listen-peer-urls http://0.0.0.0:2380 \
  --listen-client-urls http://xxxxxx:2379,http://127.0.0.1:2379 \
  --advertise-client-urls http://xxxxxx:2379 \
  --data-dir /data0/etcd/data --wal-dir /data0/etcd/wal \
  --discovery https://discovery.etcd.io/3bb9f683bf404501e55e29e45311201e
```
### service 启动
参考 init_script
