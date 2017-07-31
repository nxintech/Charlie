### 安装
```
wget https://github.com/coreos/etcd/releases/download/v3.2.4/etcd-v3.2.4-linux-amd64.tar.gz
tar zxf etcd-v3.2.4-linux-amd64.tar.gz -C /opt/
mkdir /data0/etcd/{data,wal,logs} -p
```

### 启动
集群计划3台机器，还需要额外的etcd用于服务发现
```
# 服务发现机器的ip为 10.0.0.1, 启动一个etcd
etcd --name `hostname` \
  --listen-peer-urls http://10.0.0.1:2380 \
  --listen-client-urls http://10.0.0.1:2379,http://127.0.0.1:2379 \
  --advertise-client-urls http://10.0.0.1:2379 \
  --data-dir /data0/etcd/data --wal-dir /data0/etcd/wal
```
在 10.0.0.1 上注册新的集群，名称为nxin，台数为3
```
curl -XPUT http://10.0.0.1:2379/v2/keys/discovery/nxin/_config/size -d value=3
```
如果没有额外的etcd服务用于注册,也可以使用公共服务
```
curl https://discovery.etcd.io/new?size=3
https://discovery.etcd.io/3bb9f683bf404501e55e29e45311201e
```

分别在每台机器上以集群方式启动
```
./etcd --name `hostname` --initial-advertise-peer-urls http://<host ip>:2380 \
  --listen-peer-urls http://<host ip>:2380 \
  --listen-client-urls http://<host ip>:2379,http://127.0.0.1:2379 \
  --advertise-client-urls http://<host ip>:2379 \
  --data-dir /data0/etcd/data --wal-dir /data0/etcd/wal \
  --discovery http://10.0.0.1:2379/v2/keys/discovery/nxin
  
  # 如果是用共有注册服务
  --discovery https://discovery.etcd.io/3bb9f683bf404501e55e29e45311201e
```
### service 启动
参考 init_script
