# introduce

日志收集 pipeline
```
raw logs files --> collector --> message queue --> consumer -->  store --> UI
      | (or)                                           |
log via network                                      filter --> email/sms
```

日志通过写入文件，或者通过网络，写入collector， collector 上进行一定处理写入消息队列

collector 使用 heka， 亦可以使用 Fluentd/FileBeat/logstash 等组件

message queue 用来处理日志消息的转发， 目前使用 kafka， 也可以使用 redis 

consumer 进行消息过滤聚合报警等处理，目前使用 hindsight， 也可以自己写 kafka 消费端，

store 用来保存日志，使用 elasticsearch 也可以使用 Prometheus/MySQL

UI 使用 kinbana 也可以使用grafana



# install

## prepare
nginx access_log 如果使用文件保存, 需要 logrotate 进行日志轮询切割
```
/path_to_access_log/*.log {
    missingok
    notifempty
    daily
    rotate 30
    postrotate
        [ ! -f /path_to_nginx/logs/nginx.pid ] || kill -USR1 `cat /path_to_nginx/logs/nginx.pid`
    endscript
}
```

## 编译安装

* install gcc 4.7+
```
rpm --import http://ftp.scientificlinux.org/linux/scientific/5x/x86_64/RPM-GPG-KEYs/RPM-GPG-KEY-cern
wget -O /etc/yum.repos.d/slc6-devtoolset.repo http://linuxsoft.cern.ch/cern/devtoolset/slc6-devtoolset.repo
yum install flex byacc
yum install devtoolset-2-gcc devtoolset-2-gcc-c++ devtoolset-2-binutils.x86_64 devtoolset-2-binutils-devel.x86_64
scl enable devtoolset-2 bash
```
/usr/bin/c++ 要指向安装好的位置
```
mv /usr/bin/c++ /usr/bin/c++.bak
ln -s /opt/rh/devtoolset-2/root/usr/bin/c++ /usr/bin/c++
```

* install cmake 3.5+
```
wget https://cmake.org/files/v3.7/cmake-3.7.1-Linux-x86_64.tar.gz
tar zxvf cmake-3.7.1-Linux-x86_64.tar.gz 
cp cmake-3.7.1-Linux-x86_64/bin/cmake /usr/bin/
cp cmake-3.7.1-Linux-x86_64/bin/ccmake /usr/bin/
cp -r cmake-3.7.1-Linux-x86_64/share/cmake-3.7/ /usr/share/
```
* install lua_sandbox
```
git clone https://github.com/mozilla-services/lua_sandbox.git
cd lua_sandbox
mkdir release
cd release
cmake -DCMAKE_BUILD_TYPE=release ..
make
cpack -G RPM
```
* install lua_sandbox_extensions (可选)
```
# install boost
wget https://sourceforge.net/projects/boost/files/boost/1.62.0/boost_1_62_0.tar.bz2
tar jxf boost_1_62_0.tar.bz2
cd boost_1_62_0
./bootstrap.sh
./b2
./b2 install


# install parquet-cpp
# 这里要使用 trink 自己维护的版本 加入了 package 的设置
git clone https://github.com/trink/parquet-cpp/tree/cpack_support
cd parquet-cpp
git checkout cpack_support
source setup_build_env.sh
cmake -DCPACK_GENERATOR=RPM .
make package
rpm -ivh parquet-cpp-0.0.1-Linux.rpm

# install librdkafka
git clone https://github.com/edenhill/librdkafka.git
cd librdkafka/packaging/rpm
yum install mock rpmbuild
make

# install libgeoip libpostgres
yum install geoip-devel postgresql-devel

# install lua_sandbox_extensions
git clone https://github.com/mozilla-services/lua_sandbox_extensions.git
cd lua_sandbox_extensions
mkdir release
cd release
# CentOS 7 以下需要关闭 systemd 
# or 修改 CMakeCache.txt 下 EXT_systemd:BOOL 的值为 OFF
cmake -DCMAKE_BUILD_TYPE=release -DENABLE_ALL_EXT=true -DEXT_systemd=off -DCPACK_GENERATOR=RPM ..
make
make packages
```


* install hindsight  (可选)
```
git clone https://github.com/mozilla-services/hindsight.git
cd hindsight 
mkdir release
cd release
cmake -DCMAKE_BUILD_TYPE=release ..
make
cpack -G RPM
```

# 二进制安装
release 目录下有打包好的 rpm，直接安装即可

# patch
使用 lua_sandbox_extensions 模块 decoders.nginx.access，如果配置文件中变量 log_format 的值包含字符串 "$upstream_addr", 那么 $upstream_addr 前面是不能使用引号引起来的，否则匹配不到 access log，详见 https://github.com/mozilla-services/lua_sandbox_extensions/issues/56

common_log_format.lua.patch 修复了这个问题
```shell
patch -p0 < common_log_format.lua.patch
```
# protobuf python

C++ implementation `protoc` `protoc.exe` already compiled,
you can compile them by run blew
```console
git clone https://github.com/google/protobuf.git
make
```
add python support
```console
cd protobuf/python
python setup.py build
python setup.py install
```

compile protobuf file
```console
protoc message.proto --python_out=.
```

# kafka decoder
before use
```console
pip install prometheus_client
pip install pyyaml ua-parser user-agents
pip install flask reuqests
```
