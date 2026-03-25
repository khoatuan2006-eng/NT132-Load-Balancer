# Load Balancing - Nginx + HAProxy

## Cấu trúc thư mục

```
d:\LoadBalance\
│
├── Server1\index.html                         ← Server chính 1 (port 8001)
├── Server2\index.html                         ← Server chính 2 (port 8002)
├── Server3\index.html                         ← Server backup   (port 8003)
│
├── nginx-1.29.6\conf\                         ← NGINX (Level 1-3, Windows)
│   ├── nginx.conf                                File chính
│   └── features\
│       ├── upstream.conf                         Nhóm backend servers
│       ├── rate-limit.conf                       Chống DDoS
│       └── proxy.conf                            Proxy headers + cache
│
├── backend\                                   ← Flask backend (Level 2)
│   ├── app.py                                   Entry point, khởi tạo Flask
│   ├── requirements.txt                         Thư viện cần cài (flask)
│   ├── routes\
│   │   ├── health.py                            GET /health — trạng thái server
│   │   ├── info.py                              GET /info — hostname, port, uptime
│   │   └── stress.py                            GET /stress — giả lập CPU load
│   └── utils\
│       └── stats.py                             Đếm request, tính uptime
│
├── dashboard\                                 ← Dashboard (Level 3)
│   ├── index.html
│   └── api.py
│
├── ha\                                        ← HA + HAProxy (Level 4, Ubuntu VM)
│   ├── haproxy.cfg                               Config HAProxy
│   ├── keepalived-master.conf                    Keepalived MASTER (VM1)
│   ├── keepalived-backup.conf                    Keepalived BACKUP (VM2)
│   ├── check_haproxy.sh                          Script kiểm tra HAProxy
│   └── vm-setup.md                               Hướng dẫn cài VM
│
├── docker-compose.yml                         ← Docker (Level 5)
├── Dockerfile
└── README.md
```

---

## Kiến trúc hệ thống (HAProxy + Nginx)

```
Client
  │
  ▼
[Virtual IP: 192.168.1.100]          ← Keepalived quản lý
  │
  ├─── HAProxy (VM1 - MASTER) ──┬── Nginx Node1 ──┬── Backend 1 (:8001)
  │                              │                  └── Backend 2 (:8002)
  │                              │
  │                              └── Nginx Node2 ──┬── Backend 3 (:8001)
  │                                                 └── Backend 4 (:8002)
  │
  └─── HAProxy (VM2 - BACKUP)   ← Chờ sẵn, tự động lên khi VM1 chết
```

---

## Hướng dẫn phát triển theo Level

| Level | Vai trò trong Load Balancing | Hệ điều hành |
|---|---|---|
| **Level 1** | Cấu hình **cách chia tải** bằng Nginx | Windows |
| **Level 2** | Backend để **load balancing hoạt động thực tế** | Windows |
| **Level 3** | **Giám sát** load balancing | Windows |
| **Level 4** | **HAProxy + Keepalived** — 2 lớp LB + HA | Ubuntu VM |
| **Level 5** | **Đóng gói** toàn bộ hệ thống | Docker |

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

### Level 2 — Backend thực tế (Flask)

| Tính năng | Nằm ở file | Mô tả |
|---|---|---|
| Flask app (entry point) | `backend\app.py` | Khởi tạo Flask, import routes |
| Health check API | `backend\routes\health.py` | Endpoint `/health` |
| Server info API | `backend\routes\info.py` | Endpoint `/info` — hostname, port, uptime |
| Stress test API | `backend\routes\stress.py` | Endpoint `/stress` — giả lập CPU load |
| Utilities | `backend\utils\stats.py` | Đếm request, tính uptime |
| Dependencies | `backend\requirements.txt` | `flask` |

---

### Level 3 — Dashboard Monitoring

| Tính năng | Nằm ở file | Mô tả |
|---|---|---|
| Giao diện dashboard | `dashboard\index.html` | Trạng thái server real-time |
| API lấy dữ liệu | `dashboard\api.py` | Gọi /health các backend |

---

### Level 4 — HA (HAProxy + Keepalived trên Ubuntu VM)

| # | Tính năng | Nằm ở file | Mô tả |
|---|---|---|---|
| 1 | HAProxy frontend | `ha\haproxy.cfg` | Nhận request từ client (port 80) |
| 2 | HAProxy backend | `ha\haproxy.cfg` | Phân tải tới các Nginx node |
| 3 | HAProxy health check | `ha\haproxy.cfg` | Kiểm tra Nginx node còn sống không |
| 4 | HAProxy stats page | `ha\haproxy.cfg` | Dashboard HAProxy có sẵn (port 8404) |
| 5 | HAProxy thuật toán LB | `ha\haproxy.cfg` | `roundrobin`, `leastconn`, `source` |
| 6 | Keepalived MASTER | `ha\keepalived-master.conf` | VM1, priority 101, giữ VIP |
| 7 | Keepalived BACKUP | `ha\keepalived-backup.conf` | VM2, priority 100, chờ sẵn |
| 8 | Health check script | `ha\check_haproxy.sh` | Kiểm tra HAProxy → chuyển VIP |
| 9 | Hướng dẫn cài VM | `ha\vm-setup.md` | Cài Ubuntu, HAProxy, Keepalived |

---

### Level 5 — Docker

| Tính năng | Nằm ở file | Mô tả |
|---|---|---|
| Docker Compose | `docker-compose.yml` | Khởi động hệ thống bằng 1 lệnh |
| Dockerfile | `Dockerfile` | Đóng gói backend + nginx |
