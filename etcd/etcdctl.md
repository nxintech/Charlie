API reference https://coreos.com/etcd/docs/latest/dev-guide/api_reference_v3.html

etcdctl https://github.com/coreos/etcd/blob/master/Documentation/dev-guide/interacting_v3.md

grpc gateway https://github.com/coreos/etcd/blob/master/Documentation/dev-guide/api_grpc_gateway.md

base64 tool http://tool.oschina.net/encrypt?type=3

json format http://tool.oschina.net/codeformat/json
# KV
```
./etcdctl get key --prefix| -w (fields|json)
```

range
```
curl -L http://10.211.12.18:2379/v3alpha/kv/range -X POST -d \
'{"key":"L3Vwc3RyZWFtcy9hcGlfZ2F0ZXdheQ==","range_end":"L3Vwc3RyZWFtcy9hcGlfZ2F0ZXdheg=="}'

{
    "header": {
        "cluster_id": "4246252981769682423", 
        "member_id": "6101721654483421458", 
        "revision": "1024", 
        "raft_term": "135"
    }, 
    "kvs": [
        {
            "key": "L3Vwc3RyZWFtcy9hcGlfZ2F0ZXdheS8xMC4yMTEuMTkuMTg6ODA4MA==", 
            "create_revision": "1021", 
            "mod_revision": "1023", 
            "version": "2", 
            "value": "eyJ3ZWlnaHQiOjEsICJtYXhfZmFpbHMiOjIsICJmYWlsX3RpbWVvdXQiOjEwfQ=="
        }, 
        {
            "key": "L3Vwc3RyZWFtcy9hcGlfZ2F0ZXdheS8xMC4yMTEuMTkuMjE6ODA4MA==", 
            "create_revision": "1018", 
            "mod_revision": "1022", 
            "version": "3", 
            "value": "eyJ3ZWlnaHQiOjEsICJtYXhfZmFpbHMiOjIsICJmYWlsX3RpbWVvdXQiOjEwfQ=="
        }
    ], 
    "count": "2"
}
```


# TXN
```
./etcdctl get /upstreams/api_gateway --prefix

# add
./etcdctl txn <<<'
put /upstreams/api_gateway/10.211.19.188:8080 {"weight":1,"max_fails":1,"fail_timeout":10}
put /upstreams/api_gateway/10.211.19.189:8080 {"weight":1,"max_fails":1,"fail_timeout":10}

'

# update
./etcdctl txn <<<'
put /upstreams/api_gateway/10.211.19.188:8080 {"weight":2,"max_fails":2,"fail_timeout":10}
put /upstreams/api_gateway/10.211.19.189:8080 {"weight":2,"max_fails":2,"fail_timeout":10}

'

# delete
./etcdctl txn <<<'
del /upstreams/api_gateway/10.211.19.188:8080
del /upstreams/api_gateway/10.211.19.189:8080

'
```

# Watch
```
curl http://10.211.12.18:2379/v3alpha/watch -X POST -d \
'{"create_request": {"key":"L3Vwc3RyZWFtcy9hcGlfZ2F0ZXdheQ==","range_end":"L3Vwc3RyZWFtcy9hcGlfZ2F0ZXdheg==","prev_kv":true}}'

--- create watch result
{
    "result": {
        "header": {
            "cluster_id": "4246252981769682423", 
            "member_id": "6101721654483421458", 
            "revision": "1037", 
            "raft_term": "143"
        }, 
        "created": true
    }
}

--- watch event:
# one key add
{
    "result": {
        "header": {
            "cluster_id": "4246252981769682423", 
            "member_id": "6101721654483421458", 
            "revision": "1038", 
            "raft_term": "143"
        }, 
        "events": [
            {
                "kv": {
                    "key": "key", 
                    "create_revision": "1038", 
                    "mod_revision": "1038", 
                    "version": "1", 
                    "value": "value"
                }
            }
        ]
    }
}

# one key update
{
    "result": {
        "header": {
            "cluster_id": "4246252981769682423", 
            "member_id": "6101721654483421458", 
            "revision": "1042", 
            "raft_term": "143"
        }, 
        "events": [
            {
                "kv": {
                    "key": "key", 
                    "create_revision": "1041", 
                    "mod_revision": "1042", 
                    "version": "2", 
                    "value": "new value"
                }, 
                "prev_kv": {
                    "key": "key", 
                    "create_revision": "1041", 
                    "mod_revision": "1041", 
                    "version": "1", 
                    "value": "prev value"
                }
            }
        ]
    }
}

# one key del
{
    "result": {
        "header": {
            "cluster_id": "4246252981769682423", 
            "member_id": "6101721654483421458", 
            "revision": "1040", 
            "raft_term": "143"
        }, 
        "events": [
            {
                "type": "DELETE", 
                "kv": {
                    "key": "key", 
                    "mod_revision": "1040"
                }
            }
        ]
    }
}

# txn add (add 2 keys)
{
    "result": {
        "header": {
            "cluster_id": "4246252981769682423",
            "member_id": "6101721654483421458",
            "revision": "1060",
            "raft_term": "152"
        },
        "events": [
            {
                "kv": {
                    "key": "key1",
                    "create_revision": "1060",
                    "mod_revision": "1060",
                    "version": "1",
                    "value": "value1"
                }
            },
            {
                "kv": {
                    "key": "key2",
                    "create_revision": "1060",
                    "mod_revision": "1060",
                    "version": "1",
                    "value": "value2"
                }
            }
        ]
    }
}

# txn update
{
    "result": {
        "header": {
            "cluster_id": "4246252981769682423",
            "member_id": "6101721654483421458",
            "revision": "1061",
            "raft_term": "153"
        },
        "events": [
            {
                "kv": {
                    "key": "key1",
                    "create_revision": "1060",
                    "mod_revision": "1061",
                    "version": "2",
                    "value": "value"
                },
                "prev_kv": {
                    "key": "key1",
                    "create_revision": "1060",
                    "mod_revision": "1060",
                    "version": "1",
                    "value": "value"
                }
            },
            {
                "kv": {
                    "key": "key2",
                    "create_revision": "1060",
                    "mod_revision": "1061",
                    "version": "2",
                    "value": "value2"
                },
                "prev_kv": {
                    "key": "key2",
                    "create_revision": "1060",
                    "mod_revision": "1060",
                    "version": "1",
                    "value": "value2"
                }
            }
        ]
    }
}

# txn del
{
    "result": {
        "header": {
            "cluster_id": "4246252981769682423", 
            "member_id": "6101721654483421458", 
            "revision": "1062", 
            "raft_term": "153"
        }, 
        "events": [
            {
                "type": "DELETE", 
                "kv": {
                    "key": "L3Vwc3RyZWFtcy9hcGlfZ2F0ZXdheS8xMC4yMTEuMTkuMTg4OjgwODA=", 
                    "mod_revision": "1062"
                }, 
                "prev_kv": {
                    "key": "L3Vwc3RyZWFtcy9hcGlfZ2F0ZXdheS8xMC4yMTEuMTkuMTg4OjgwODA=", 
                    "create_revision": "1060", 
                    "mod_revision": "1061", 
                    "version": "2", 
                    "value": "eyJ3ZWlnaHQiOjIsIm1heF9mYWlscyI6MiwiZmFpbF90aW1lb3V0IjoxMH0="
                }
            }, 
            {
                "type": "DELETE", 
                "kv": {
                    "key": "L3Vwc3RyZWFtcy9hcGlfZ2F0ZXdheS8xMC4yMTEuMTkuMTg5OjgwODA=", 
                    "mod_revision": "1062"
                }, 
                "prev_kv": {
                    "key": "L3Vwc3RyZWFtcy9hcGlfZ2F0ZXdheS8xMC4yMTEuMTkuMTg5OjgwODA=", 
                    "create_revision": "1060", 
                    "mod_revision": "1061", 
                    "version": "2", 
                    "value": "eyJ3ZWlnaHQiOjIsIm1heF9mYWlscyI6MiwiZmFpbF90aW1lb3V0IjoxMH0="
                }
            }
        ]
    }
}
```