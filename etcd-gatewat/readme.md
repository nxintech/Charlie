官方仓库已经编提供了 etcd 的 grpc-gateway 库
https://github.com/coreos/etcd/blob/master/etcdserver/etcdserverpb/gw/rpc.pb.gw.go

经测试但是不能使用在go1.8.3，所以要手动编译 rpc.proto

# manully compile
## install protoc
wget https://github.com/google/protobuf/releases/download/v3.4.0/protoc-3.4.0-linux-x86_64.zip


## install grpc
```
go get golang.org/x/net
go get golang.org/x/text
go get google.golang.org/grpc
```

上面的依赖包需要翻墙，下面是不翻墙的下载方法
```
go get github.com/golang/net
go get github.com/golang/text
mkdir $GOPATH/src/golang.org/x -p
mv $GOPATH/src/github.com/golang/net $GOPATH/src/golang.org/x/
mv $GOPATH/src/github.com/golang/text $GOPATH/src/golang.org/x/

go get github.com/grpc/grpc-go
mkdir $GOPATH/src/google.golang.org
mv $GOPATH/src/github.com/grpc/grpc-go $GOPATH/src/google.golang.org/grpc

go get github.com/google/go-genproto
mv $GOPATH/src/github.com/google/go-genproto $GOPATH/src/google.golang.org/genproto
```

## install grpc-gateway
```
go get -u github.com/grpc-ecosystem/grpc-gateway/protoc-gen-grpc-gateway
go get -u github.com/grpc-ecosystem/grpc-gateway/protoc-gen-swagger
go get -u github.com/golang/protobuf/protoc-gen-go
```

## compile etcd proto
编译 rpc.proto

```
go get github.com/gogo/protobuf
go get github.com/google/protobuf
go get github.com/coreos/etcd/mvcc
go get github.com/coreos/etcd/auth
go get github.com/coreos/etcd/etcdserver/etcdserverpb


cd $GOPATH/src/github.com/coreos
# include 目录是 protoc 的include

protoc -I./include -I. -I$GOPATH/src \
-I$GOPATH/src/github.com/coreos \
-I$GOPATH/src/github.com/gogo/protobuf \
-I$GOPATH/src/github.com/google/protobuf/src \
-I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/go
--grpc-gateway_out=logtostderr=true:. \
etcd/etcdserver/etcdserverpb/rpc.proto

# for go 
--go_out=plugins=grpc:.
```
