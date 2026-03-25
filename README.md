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

> **Mục tiêu:** Thay thế `python -m http.server` (chỉ serve HTML tĩnh) bằng Flask app thực sự,
> có API để Nginx kiểm tra sức khỏe server, xem thông tin, và test hiệu năng.
>
> **Tại sao cần?** Ở Level 1, backend chỉ là trang HTML tĩnh — không có logic gì.
> Level 2 biến mỗi backend thành một ứng dụng thực tế mà Nginx có thể load balance.

**Cài đặt:**
```bash
cd backend
pip install -r requirements.txt
```

**Chạy:** (thay port 8001/8002 tùy server)
```bash
python app.py --port 8001
python app.py --port 8002
```

| File | Người phụ trách | Việc cần làm |
|---|---|---|
| `backend\app.py` | — | Khởi tạo Flask app, import route từ `routes/`, nhận `--port` từ command line |
| `backend\routes\health.py` | — | Tạo endpoint `GET /health` |
| `backend\routes\info.py` | — | Tạo endpoint `GET /info` |
| `backend\routes\stress.py` | — | Tạo endpoint `GET /stress` |
| `backend\utils\stats.py` | — | Hàm tiện ích dùng chung cho các route |
| `backend\requirements.txt` | ✅ Đã có | Chỉ chứa `flask` |

**Chi tiết từng endpoint:**

#### 1. `GET /health` → `routes/health.py`
Nginx gọi endpoint này để kiểm tra server còn sống không (health check).

```
Request:  GET http://localhost:8001/health
Response: {"status": "ok"}        ← HTTP 200
          {"status": "unhealthy"} ← HTTP 503 (nếu server có vấn đề)
```

#### 2. `GET /info` → `routes/info.py`
Trả về thông tin server — dùng để xác nhận Nginx đang gửi request tới server nào.

```
Request:  GET http://localhost:8001/info
Response: {
    "server": "Server1",
    "port": 8001,
    "hostname": "DESKTOP-ABC123",
    "uptime": "00:05:32",
    "total_requests": 42
}
```

#### 3. `GET /stress` → `routes/stress.py`
Giả lập server bận (tính toán nặng) — dùng để test xem Nginx có phân tải đều không khi server bị chậm.

```
Request:  GET http://localhost:8001/stress?seconds=2
Response: {
    "server": "Server1",
    "task": "CPU stress test",
    "duration": "2.00s",
    "result": "completed"
}
```

#### 4. `utils/stats.py`
Hàm dùng chung, ví dụ:
- `get_uptime()` → tính thời gian server đã chạy
- `count_request()` → đếm tổng số request đã nhận
- `get_stats()` → trả về dict tổng hợp

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
