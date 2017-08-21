package main

import (
	"flag"
	"net/http"
  
	"golang.org/x/net/context"
  	"google.golang.org/grpc"
  	"github.com/golang/glog"
	"github.com/grpc-ecosystem/grpc-gateway/runtime"

	"github.com/coreos/etcd/etcdserver/etcdserverpb/gw"
)

var (
	echoEndpoint = flag.String("endpoint", "localhost:9090", "endpoint of etcd")
)

func run() error {
	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	mux := runtime.NewServeMux()
	opts := []grpc.DialOption{grpc.WithInsecure()}
	err := gw.RegisterKVHandlerFromEndpoint(ctx, mux, *echoEndpoint, opts)
	if err != nil {
		return err
	}
	err = gw.RegisterWatchHandlerFromEndpoint(ctx, mux, *echoEndpoint, opts)
	if err != nil {
		return err
	}

	return http.ListenAndServe(":8080", mux)
}

func main() {
	flag.Parse()
	defer glog.Flush()

	if err := run(); err != nil {
		glog.Fatal(err)
	}
}
