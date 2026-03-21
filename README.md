# Load Balancing - Nginx

## Cấu trúc thư mục

```
d:\LoadBalance\
│
├── Server1\index.html              ← Server chính 1 (port 8001)
├── Server2\index.html              ← Server chính 2 (port 8002)
├── Server3\index.html              ← Server backup   (port 8003)
│
├── nginx-1.29.6\conf\
│   ├── nginx.conf                  ← File chính (khung sườn)
│   └── features\                   ← Mỗi file = 1 nhóm tính năng
│       ├── upstream.conf               Nhóm backend servers
│       ├── rate-limit.conf             Chống DDoS
│       └── proxy.conf                  Proxy headers + cache
│
└── README.md                       ← File này
```

---

## Hướng dẫn phát triển theo Level

| Level | Vai trò trong Load Balancing |
|---|---|
| **Level 1** | Cấu hình **cách chia tải** (thuật toán, health check, backup) |
| **Level 2** | Backend có `/health`, `/stress` để **load balancing hoạt động thực tế** hơn |
| **Level 3** | **Giám sát** load balancing đang chia tải như thế nào |
| **Level 4** | Đảm bảo **bản thân Nginx (load balancer) không chết** |
| **Level 5** | **Đóng gói** toàn bộ hệ thống load balancing |

---

### Level 1 — Nâng cấp Nginx Config

| # | Tính năng | Nằm ở file | Cú pháp |
|---|---|---|---|
| 1 | Weighted Round Robin | `nginx-1.29.6\conf\features\upstream.conf` | `weight=3` |
| 2 | Sticky Session | `nginx-1.29.6\conf\features\upstream.conf` | `ip_hash;` |
| 3 | Passive Health Check | `nginx-1.29.6\conf\features\upstream.conf` | `max_fails=3 fail_timeout=30s` |
| 4 | Backup Server | `nginx-1.29.6\conf\features\upstream.conf` | `server ... backup;` |
| 5 | Rate Limiting | `nginx-1.29.6\conf\features\rate-limit.conf` | `limit_req_zone ...` |
| - | Proxy headers, no-cache | `nginx-1.29.6\conf\features\proxy.conf` | `proxy_set_header ...` |
| - | Khung sườn (include) | `nginx-1.29.6\conf\nginx.conf` | `include features/...` |
| - | Trang backup server | `Server3\index.html` | HTML |

---

### Level 2 — Backend thực tế (Flask/FastAPI)

| Tính năng | Nằm ở file | Mô tả |
|---|---|---|
| Flask app | `backend\app.py` | Thay `python http.server` |
| Health check API | `backend\app.py` | Endpoint `/health` |
| Server info API | `backend\app.py` | Endpoint `/info` |
| Stress test API | `backend\app.py` | Endpoint `/stress` |

---

### Level 3 — Dashboard Monitoring

| Tính năng | Nằm ở file | Mô tả |
|---|---|---|
| Giao diện dashboard | `dashboard\index.html` | Trạng thái server real-time |
| API lấy dữ liệu | `dashboard\api.py` | Gọi /health các backend |

---

### Level 4 — HA (High Availability)

| Tính năng | Nằm ở file | Mô tả |
|---|---|---|
| Keepalived MASTER | `ha\keepalived-master.conf` | VM1, priority cao |
| Keepalived BACKUP | `ha\keepalived-backup.conf` | VM2, priority thấp |

---

### Level 5 — Docker

| Tính năng | Nằm ở file | Mô tả |
|---|---|---|
| Docker Compose | `docker-compose.yml` | Khởi động hệ thống bằng 1 lệnh |
| Dockerfile | `Dockerfile` | Đóng gói backend + nginx |

