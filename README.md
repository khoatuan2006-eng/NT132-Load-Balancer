# Load Balancing — HAProxy + Keepalived

## Tổng quan

Hệ thống Load Balancing sử dụng **HAProxy** làm bộ chia tải chính, kết hợp **Keepalived** để đảm bảo High Availability (HA). Toàn bộ load balancer chạy trên **Ubuntu VM**, backend chạy trên **Windows**.

## Cấu trúc thư mục

```
d:\LoadBalance\
│
├── Server1\index.html                         ← Backend 1 (port 8001)
├── Server2\index.html                         ← Backend 2 (port 8002)
├── Server3\index.html                         ← Backend backup (port 8003)
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
├── ha\                                        ← HAProxy + Keepalived (Level 1 + 4)
│   ├── haproxy.cfg                              Config HAProxy (chia tải + stats)
│   ├── keepalived-master.conf                   Keepalived MASTER (VM1)
│   ├── keepalived-backup.conf                   Keepalived BACKUP (VM2)
│   ├── check_haproxy.sh                         Script kiểm tra HAProxy
│   └── vm-setup.md                              Hướng dẫn cài VM
│
├── dashboard\                                 ← Dashboard tùy chỉnh (Level 3)
│   ├── index.html
│   └── api.py
│
├── docker-compose.yml                         ← Docker (Level 5)
├── Dockerfile
├── start.bat                                  ← Khởi động backend trên Windows
├── stop.bat                                   ← Tắt backend
└── README.md
```

---

## Kiến trúc hệ thống

```
                          ┌──────────────────────────────────┐
                          │        MÁY WINDOWS               │
  Client (trình duyệt)   │                                   │
       │                  │   Backend 1 (:8001)               │
       ▼                  │   Backend 2 (:8002)               │
┌──────────────┐          │   Backend 3 (:8003) backup        │
│  Virtual IP  │          └────────┬──────┬──────┬────────────┘
│192.168.56.100│                   ▲      ▲      ▲
└──────┬───────┘                   │      │      │
       │                     Chuyển tiếp request
  ┌────▼──────┐                    │      │      │
  │  HAProxy  │────────────────────┴──────┴──────┘
  │  (trên VM)│
  └────┬──────┘
       │
 ┌─────┴──────┐
 VM1          VM2
(MASTER)    (BACKUP)
HAProxy     HAProxy          ← VM1 chết → VM2 tự động lên
Keepalived  Keepalived
```

**Luồng request:**
1. Client truy cập **Virtual IP** (192.168.56.100:80)
2. Keepalived đảm bảo VIP luôn trỏ tới VM đang sống
3. **HAProxy** nhận request → chia tải tới các Backend trên Windows
4. Backend xử lý → trả kết quả cho Client

---

## Hướng dẫn phát triển theo Level

| Level | Nội dung | Chạy trên |
|---|---|---|
| **Level 1** | Cấu hình **chia tải** bằng HAProxy | Ubuntu VM |
| **Level 2** | Backend **Flask** để load balancing hoạt động thực tế | Windows |
| **Level 3** | **Giám sát** hệ thống (HAProxy Stats + Dashboard) | Ubuntu VM + Windows |
| **Level 4** | **Keepalived** — HA, tự phục hồi khi HAProxy chết | Ubuntu VM |
| **Level 5** | **Docker** — đóng gói toàn bộ hệ thống | Docker |
| **Level 6** ⭐ | **Cascading Failure Prevention** — chống sụp đổ dây chuyền | Ubuntu VM + Windows |
| **Level 7** 🧠 | **AI-Driven Load Balancing** — học máy tăng cường bảo vệ hệ thống | Ubuntu VM + Windows |

---

### Level 1 — HAProxy Load Balancing

> **Mục tiêu:** Cấu hình HAProxy chia tải request tới các backend server trên Windows.
> HAProxy thay thế vai trò của Nginx — làm load balancer chính cho hệ thống.

**Tất cả tính năng nằm trong 1 file:** `ha/haproxy.cfg`

| # | Tính năng | Mô tả | Cú pháp HAProxy |
|---|---|---|---|
| 1 | Round Robin | Chia đều request lần lượt cho các server | `balance roundrobin` |
| 2 | Weighted Round Robin | Server1 nhận nhiều hơn Server2 (tỉ lệ 3:1) | `weight 3` / `weight 1` |
| 3 | Active Health Check | Kiểm tra server còn sống không (mỗi 3 giây) | `check inter 3s fall 3 rise 2` |
| 4 | Backup Server | Server3 chỉ lên khi Server1 + Server2 đều chết | `backup` |
| 5 | Rate Limiting | Chặn IP gửi quá nhiều request (chống DDoS) | `stick-table` + `http-request deny` |
| 6 | Stats Page | Trang web theo dõi trạng thái tất cả server | `listen stats` (port 8404) |

**Cách chạy:**

1. Chạy backend trên Windows:
   ```
   start.bat
   ```

2. SSH vào VM, copy config và khởi động HAProxy:
   ```bash
   sudo cp haproxy.cfg /etc/haproxy/haproxy.cfg
   sudo systemctl restart haproxy
   ```

3. Truy cập từ Windows:
   - Load Balancer: `http://192.168.56.100` (qua VIP) hoặc `http://<IP_VM>` (trực tiếp)
   - Stats page: `http://<IP_VM>:8404/stats` (login: admin / admin123)

**Cách test:**
1. Mở trình duyệt → `http://<IP_VM>` → F5 liên tục → thấy Server1/Server2 xen kẽ
2. Tắt Server1 trên Windows → F5 → chỉ còn Server2 (health check loại Server1)
3. Tắt Server2 → F5 → **Server3 BACKUP tự động lên thay**
4. Bật lại Server1/Server2 → Server3 tự nghỉ

**Phân công:**

| Người | Viết phần | Trong file |
|---|---|---|
| **Người 1** | Frontend + Backend (chia tải + health check) | `ha/haproxy.cfg` |
| **Người 2** | Rate Limiting (chống DDoS) | `ha/haproxy.cfg` |
| **Người 3** | Stats page (trang giám sát) | `ha/haproxy.cfg` |

---

### Level 2 — Backend thực tế (Flask)

> **Mục tiêu:** Thay thế `python -m http.server` (chỉ serve HTML tĩnh) bằng Flask app thực sự,
> có API để HAProxy kiểm tra sức khỏe server, xem thông tin, và test hiệu năng.
>
> **Tại sao cần?** Ở Level 1, backend chỉ là trang HTML tĩnh — không có logic gì.
> Level 2 biến mỗi backend thành một ứng dụng thực tế mà HAProxy có thể load balance.

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
| `backend\app.py` | ✅ Đã có | Khởi tạo Flask app, import route từ `routes/`, nhận `--port` từ command line |
| `backend\routes\health.py` | — | Tạo endpoint `GET /health` |
| `backend\routes\info.py` | — | Tạo endpoint `GET /info` |
| `backend\routes\stress.py` | — | Tạo endpoint `GET /stress` |
| `backend\utils\stats.py` | ✅ Đã có | `count_request()`, `get_uptime()`, `get_stats()` |
| `backend\requirements.txt` | ✅ Đã có | Chỉ chứa `flask` |

**Chi tiết từng endpoint:**

#### 1. `GET /health` → `routes/health.py`
HAProxy gọi endpoint này để kiểm tra server còn sống không (health check).

```
Request:  GET http://localhost:8001/health
Response: {"status": "ok"}        ← HTTP 200
          {"status": "unhealthy"} ← HTTP 503 (nếu server có vấn đề)
```

#### 2. `GET /info` → `routes/info.py`
Trả về thông tin server — dùng để xác nhận HAProxy đang gửi request tới server nào.

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
Giả lập server bận — dùng để test xem HAProxy có phân tải đều không khi server bị chậm.

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

### Level 3 — Monitoring (Giám sát)

> **Mục tiêu:** Giám sát trạng thái hệ thống load balancing theo thời gian thực.

#### 3a. HAProxy Stats Page (có sẵn, không cần code)

HAProxy cung cấp **sẵn** trang giám sát tại `http://<IP_VM>:8404/stats`:
- Trạng thái mỗi backend server (UP/DOWN)
- Số request đã xử lý
- Thời gian phản hồi trung bình
- Lượng traffic (bytes in/out)
- Tự động refresh mỗi 5 giây

Login: `admin` / `admin123`

#### 3b. Custom Dashboard (tùy chọn, điểm cộng)

| Tính năng | Nằm ở file | Mô tả |
|---|---|---|
| Giao diện dashboard | `dashboard\index.html` | Trạng thái server real-time |
| API lấy dữ liệu | `dashboard\api.py` | Gọi /health các backend + HAProxy stats API |

---

### Level 4 — High Availability (Keepalived)

> **Mục tiêu:** Nếu HAProxy trên VM1 chết → VM2 tự động lên thay.
> Client truy cập qua 1 Virtual IP duy nhất, không cần biết VM nào đang hoạt động.

**Yêu cầu:** Mỗi người tự setup 2 VM Ubuntu trên máy mình theo `ha/vm-setup.md`.

**Phân công viết config:**

| Người | Viết file | Mục tiêu |
|---|---|---|
| **Người 1** | `ha\keepalived-master.conf` | Config Keepalived cho VM1 — MASTER, priority 101, giữ VIP |
| **Người 2** | `ha\keepalived-backup.conf` | Config Keepalived cho VM2 — BACKUP, priority 100, chờ sẵn |
| **Người 3** | `ha\check_haproxy.sh` | Script bash kiểm tra HAProxy còn chạy không |

**Mỗi người đều phải tự làm trên máy mình:**

1. ✅ Setup 2 VM Ubuntu theo `ha/vm-setup.md`
2. ✅ Cấu hình mạng (Bridged hoặc NAT + Host-Only)
3. ✅ Cài `haproxy` + `keepalived` trên cả 2 VM
4. ✅ Pull config từ GitHub → paste vào VM
5. ✅ Test failover: tắt HAProxy trên VM1 → VIP tự chuyển sang VM2
6. ✅ Quay video demo kết quả

**Deploy lên VM:**

```bash
# Trên CẢ 2 VM:
sudo cp haproxy.cfg /etc/haproxy/haproxy.cfg
sudo cp check_haproxy.sh /etc/keepalived/check_haproxy.sh
sudo chmod +x /etc/keepalived/check_haproxy.sh

# Trên VM1 (Master):
sudo cp keepalived-master.conf /etc/keepalived/keepalived.conf

# Trên VM2 (Backup):
sudo cp keepalived-backup.conf /etc/keepalived/keepalived.conf

# Khởi động (cả 2 VM):
sudo systemctl restart haproxy
sudo systemctl restart keepalived
```

**Test failover:**

```bash
# 1. Kiểm tra VIP đang ở VM1
ip addr show enp0s8        # Thấy 192.168.56.100 = đúng

# 2. Tắt HAProxy trên VM1
sudo systemctl stop haproxy

# 3. Kiểm tra VIP đã chuyển sang VM2
# Trên VM2: ip addr show enp0s8    # Thấy 192.168.56.100 = failover thành công!

# 4. Bật lại HAProxy trên VM1
sudo systemctl start haproxy
# VIP tự chuyển về VM1 (priority cao hơn)
```

**Bảng tổng hợp file:**

| # | File | Mô tả |
|---|---|---|
| 1 | `ha\haproxy.cfg` | Load Balancing + Stats page (Level 1 + 3) |
| 2 | `ha\keepalived-master.conf` | VM1, priority 101, giữ VIP |
| 3 | `ha\keepalived-backup.conf` | VM2, priority 100, chờ sẵn |
| 4 | `ha\check_haproxy.sh` | Kiểm tra HAProxy → chuyển VIP |
| 5 | `ha\vm-setup.md` | ✅ Đã có — cài VirtualBox, Ubuntu, mạng |

---

### Level 5 — Docker

| Tính năng | Nằm ở file | Mô tả |
|---|---|---|
| Docker Compose | `docker-compose.yml` | Khởi động hệ thống bằng 1 lệnh |
| Dockerfile | `Dockerfile` | Đóng gói backend + HAProxy |

---

### Level 6 — Cascading Failure Prevention ⭐ (Tính năng tâm huyết)

> **Mục tiêu:** Giải quyết vấn đề **sụp đổ dây chuyền** (cascading failure) — nguyên nhân #1
> gây sập hệ thống lớn như Facebook (2021), AWS (2017), Google Cloud (2020).
>
> **Tham khảo:**
> - Google SRE Book — Ch.21: *Handling Overload*
> - Google SRE Book — Ch.22: *Addressing Cascading Failures*
> - Netflix Hystrix — Circuit Breaker Pattern
>
> **Liên hệ CCNA:** VRRP (Keepalived) tương đương HSRP (Cisco) — cùng nguyên lý
> redundancy và failover, ứng dụng thực tế trên Linux.

#### Vấn đề cần giải quyết

```
Hệ thống KHÔNG có protection:
  Server1 chết → Server2 gánh gấp đôi → QUÁ TẢI → Server2 CHẾT
  → Server3 (backup) gánh tất cả → QUÁ TẢI → Server3 CHẾT
  → CẢ HỆ THỐNG SẬP HOÀN TOÀN (cascading failure)

Hệ thống CÓ protection:
  Server1 chết → Server2 nhận thêm traffic
  → NHƯNG maxconn giới hạn → Server2 chỉ nhận đủ sức
  → Request dư → trả "503 Hệ thống bận" (graceful degradation)
  → Server2 VẪN SỐNG, vẫn phục vụ bình thường ✅
  → Server1 restart → slow start → tăng dần 10% → 100%
  → Hệ thống TỰ PHỤC HỒI ✅
```

#### 4 tính năng chống Cascading Failure

| # | Tính năng | Mô tả | Config |
|---|---|---|---|
| 1 | **Maxconn Protection** | Giới hạn số kết nối mỗi server — thà trả 503 còn hơn để server chết | `maxconn 100` per server |
| 2 | **Slow Start** | Server restart → nhận 10% traffic → tăng dần → 100% trong 30s | `slowstart 30s` |
| 3 | **Request Priority** | Khi overload: giữ `/health`, `/info` (quan trọng), drop `/stress` (thấp) | HAProxy ACL rules |
| 4 | **Graceful Degradation** | Server quá tải → trả response rút gọn thay vì timeout | Flask middleware |

#### Cách test — SO SÁNH trước/sau

**Test 1: KHÔNG có protection (chứng minh vấn đề)**

```bash
# 1. Tắt maxconn, slowstart trong haproxy.cfg
# 2. Chạy load test (gửi 1000 request/s)
# 3. Kill Server1
# 4. Quan sát: Server2 quá tải → response time tăng → timeout → chết
# 5. Server3 backup lên → cũng chết
# → Kết quả: HỆ THỐNG SẬP HOÀN TOÀN
```

**Test 2: CÓ protection (chứng minh giải pháp)**

```bash
# 1. Bật maxconn, slowstart, request priority
# 2. Chạy cùng load test (1000 request/s)
# 3. Kill Server1
# 4. Quan sát: Server2 giới hạn tải → trả 503 cho request dư
# 5. Server2 VẪN SỐNG, vẫn phục vụ bình thường
# 6. Server1 restart → slow start → hệ thống phục hồi
# → Kết quả: HỆ THỐNG KHÔNG SẬP
```

**Đo lường:**

| Chỉ số | Không có protection | Có protection |
|---|---|---|
| Thời gian sập toàn bộ | ~10 giây | ∞ (không sập) |
| Response time trung bình | 15ms → timeout | 15ms → 20ms (ổn định) |
| Số request thất bại | 100% (sau cascade) | ~30% (503, có kiểm soát) |
| Thời gian phục hồi | Phải restart thủ công | Tự phục hồi trong 30s |

#### Phân công nhóm

| Thành viên | Phụ trách | Chi tiết |
|---|---|---|
| **Người 1** | Detection & Config | Cấu hình `maxconn`, `slowstart`, ACL trong `haproxy.cfg` |
| **Người 2** | Testing & Measurement | Viết kịch bản test, đo lường, ghi kết quả trước/sau |
| **Người 3** | Visualization & Report | Giám sát bằng HAProxy stats + `tcpdump`, viết báo cáo tham khảo Google SRE |

#### Tài liệu tham khảo

1. **Google SRE Book** — [Ch.21: Handling Overload](https://sre.google/sre-book/handling-overload/)
2. **Google SRE Book** — [Ch.22: Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)
3. **Netflix Hystrix** — [Circuit Breaker Pattern](https://github.com/Netflix/Hystrix/wiki)
4. **Microsoft Azure** — [Circuit Breaker Design Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
5. **CCNA/CCNP** — HSRP vs VRRP comparison (Cisco vs Linux redundancy)

---

### Level 7 — AI-Driven Load Balancing 🧠 (Nghiên cứu Nâng cao)

> **Mục tiêu:** Nâng cấp Level 6 từ việc sử dụng các cấu hình tĩnh (như `maxconn` cố định) thành một **hệ thống tự học và tự thích nghi**. Sử dụng **Reinforcement Learning (Học Máy Tăng Cường - RL)** để tác tử AI tự động phát hiện tải trọng của các backend và phân bổ lại giới hạn chịu đựng (weight, maxconn) ngay lập tức nhằm ngăn ngừa sụp đổ dây chuyền.
> 
> **Định hướng:** Đề án chuyên sâu kết hợp Mạng hệ thống và Trí tuệ Nhân tạo.

#### Kiến trúc: Tách biệt Control Plane và Data Plane
- **Data Plane (HAProxy):** Vẫn làm nhiệm vụ chuyển tiếp request nguyên bản ở tốc độ cao cực đại. Được mở cổng giao tiếp API (Unix Socket).
- **Control Plane (Agent AI):** Chạy lệnh Python độc lập sử dụng thư viện `Gymnasium` và `Stable-Baselines3`. Đóng vai trò làm bộ não trung tâm quan sát 1 lần/giây để đọc các chỉ số % CPU, RAM, Response Time và ra quyết định gửi lệnh điều chỉnh xuống Socket của HAProxy.

#### Giai đoạn Thực hiện (RL Pipeline)
1. **Mở khóa tương tác phần cứng HAProxy:** Kích hoạt Runtime API thông qua `admin.sock`.
2. **Thiết kế không gian Học máy (Gym Environment):** Định nghĩa State (Tình trạng phần cứng), Action (Thay đổi tỷ lệ chéo) và Reward (Thưởng/Phạt khi server lag/chết).
3. **Mô phỏng hỗn loạn (Chaos Engineering):** Sử dụng các công cụ mạnh như `Locust` để bơm traffic cực lớn có chủ đích, tạo điểm nghẽn cổ chai mô phỏng.
4. **Huấn luyện thuật toán (Training):** Dạy mạng Neural Network (PPO hoặc DQN) chống đỡ các đợt càn quét traffic mà không để HTTP 500 rớt lại mạng.
5. **Tích hợp Tác Tử:** Đóng băng (Freeze) model suy luận và đặt lên giám sát server sản xuất.
