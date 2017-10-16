# install lua prometheus package
```
cd /usr/local/openresty/lualib
wget https://raw.githubusercontent.com/knyar/nginx-lua-prometheus/master/prometheus.lua
```

# config openresty
add `nginx.conf`
```
lua_shared_dict prometheus_metrics 10M; #init 10M memory

init_by_lua '
  prometheus = require("prometheus").init("prometheus_metrics")
  metric_requests = prometheus:counter(
    "nginx_http_requests_total", "Number of HTTP requests", {"host", "status"})
  metric_latency = prometheus:histogram(
    "nginx_http_request_duration_seconds", "HTTP request latency", {"host"})
  metric_connections = prometheus:gauge(
    "nginx_http_connections", "Number of HTTP connections", {"state"})
';
log_by_lua '
  local host = ngx.var.host:gsub("^www.", "")
  metric_requests:inc(1, {host, ngx.var.status})
  metric_latency:observe(ngx.now() - ngx.req.start_time(), {host})
';

server {
    listen 9145;
    allow <prometheus_ip>;
    deny all;
    location /metrics {
        content_by_lua 'prometheus:collect()';
    }
    access_log off;
}
```

# prometheus config
add `prometheus.yml `
```
scrape_configs:
  - job_name: 'openresty'
    static_configs:
      - targets: ['<openresty_ip>:9145']
```
reload
```
curl -X POST 127.0.0.1:9090/-/reload
```
check
```
curl 127.0.0.1:9090/api/v1/targets |grep openresty
```

# metric
https://povilasv.me/prometheus-tracking-request-duration/

TYPE nginx_http_request_duration_seconds histogram 表示直方图类型 metrics

直方图有三种 metric
* nginx_http_request_duration_seconds_bucket
* nginx_http_request_duration_seconds_sum 
* nginx_http_request_duration_seconds_count

假设 nginx_http_request_duration_seconds_bucket有 5个 bucket，分别是 0.5s,1s,2s,3s,5s，当有3个请求进来，相应时间分别是1s,2s,3s时，metric 数据会如下：
```
nginx_http_request_duration_seconds_bucket{le="0.5"} 0
nginx_http_request_duration_seconds_bucket{le="1"} 1
nginx_http_request_duration_seconds_bucket{le="2"} 2
nginx_http_request_duration_seconds_bucket{le="3"} 3
nginx_http_request_duration_seconds_bucket{le="5"} 3
nginx_http_request_duration_seconds_bucket{le="+Inf"} 3
nginx_http_request_duration_seconds_sum 6
nginx_http_request_duration_seconds_count 3
```
每个 bucket 统计的是延时小于等于 le 数值的请求个数， 注意它是累加的，也就是说 le="5" 统计的请求个数也包含了1s,2s的请求在内

sum is 1s + 2s + 3s = 6， 所以sum 统计的是所有请求的总相应时间

count 是请求个数，因为有3个请求，所以为3

那么平均请求响应时间就是
```
nginx_http_request_duration_seconds_sum / nginx_http_request_duration_seconds_count
```