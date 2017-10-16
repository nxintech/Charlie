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