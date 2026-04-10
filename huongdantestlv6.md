# 🛡️ Hướng Dẫn Test Level 6 — Cascading Failure Prevention

> **Dành cho thành viên nhóm** — Đọc hết trước khi bắt đầu chạy!  
> Level 6 mở rộng từ Level 4/5 bằng cách thêm **9 cơ chế chống lỗi dây chuyền (Cascading Failure)** vào HAProxy.

---

## 🗺️ Kiến Trúc Tổng Quan

```
[Client / Trình duyệt]
        │
        ▼
[Keepalived VIP: 192.168.56.100]   ← IP ảo, tự chuyển giữa 2 VM
        │
        ▼
[HAProxy (VM Master hoặc VM Backup)]
  ├── Rate Limiting     (cơ chế 1)
  ├── Maxconn           (cơ chế 2)
  ├── Timeout           (cơ chế 3)
  ├── Queue Limit       (cơ chế 4)
  ├── Circuit Breaker   (cơ chế 5)
  ├── Retry Control     (cơ chế 6)
  ├── Slow Start        (cơ chế 7)
  ├── Priority Routing  (cơ chế 8)
  └── Monitoring Stats  (cơ chế 9)
        │
        ├──▶ Server 1 (Windows :8001)
        ├──▶ Server 2 (Windows :8002)
        └──▶ Server 3 / Backup (Windows :8003)
```

**Windows** chạy 3 backend Flask + Dashboard API.  
**Ubuntu VM** chạy HAProxy + Keepalived.

---

## ⚙️ Yêu Cầu Môi Trường

| Thành phần | Yêu cầu |
|---|---|
| OS Windows | Python 3.8+ đã cài |
| Ubuntu VM | HAProxy 2.8+, Keepalived đã cài |
| Mạng | Windows ↔ VM thấy nhau (ping được) |
| Thư viện Python | `flask`, `flask-cors`, `requests` |

> 💡 Cài thư viện nếu chưa có:
> ```bash
> pip install flask flask-cors requests
> ```

---

## 🖥️ PHẦN 1 — CHẠY TRÊN MÁY WINDOWS

### Bước 1.1 — Kiểm tra IP Windows

Mở **CMD** và chạy:
```cmd
ipconfig
```
Tìm dòng `IPv4 Address` của card mạng kết nối với VM (thường là `192.168.56.x` hoặc `192.168.20.x`).  
**Ghi lại IP này** — cần điền vào `haproxy.cfg` ở bước sau.

---

### Bước 1.2 — Chỉnh IP trong `haproxy.cfg` (trên VM)

> Xem **Phần 2** để biết cách copy file sang VM.

Mở file `ha/haproxy.cfg`, tìm và thay **toàn bộ** `192.168.20.25` bằng IP Windows của bạn:

```
server s1 <IP_WINDOWS>:8001 check inter 3s fall 3 rise 2 maxconn 100 slowstart 30s
server s2 <IP_WINDOWS>:8002 check inter 3s fall 3 rise 2 maxconn 100 slowstart 30s
server s3 <IP_WINDOWS>:8003 check inter 3s fall 3 rise 2 maxconn 100 slowstart 30s backup
```

---

### Bước 1.3 — Chỉnh IP VM trong `start.bat`

Mở file `start.bat`, dòng 11:
```bat
set VM_IP=192.168.56.101
```
Đổi `192.168.56.101` thành IP của **VM Master** của nhóm bạn.

---

### Bước 1.4 — Khởi động toàn bộ backend

**Double-click vào file `start.bat`** hoặc chạy trong CMD:
```cmd
start.bat
```

Khi thành công, sẽ thấy **4 cửa sổ CMD** mở ra:
| Cửa sổ | Dịch vụ | Port |
|---|---|---|
| Server1 | Backend Flask | 8001 |
| Server2 | Backend Flask | 8002 |
| Server3 (Backup) | Backend Flask | 8003 |
| Dashboard API | Monitoring API | 5000 |

✅ **Kiểm tra nhanh** — mở trình duyệt, truy cập:
- http://localhost:8001 → Trang chào mừng Server 1
- http://localhost:8002 → Trang chào mừng Server 2
- http://localhost:8003 → Trang chào mừng Server 3
- http://localhost:5000 → Dashboard Monitoring

---

## 🐧 PHẦN 2 — CẤU HÌNH TRÊN UBUNTU VM

> SSH vào VM Master trước. Mở CMD trên Windows:
> ```cmd
> ssh <tên_user>@<IP_VM_MASTER>
> ```
> Ví dụ: `ssh khoa@192.168.56.101`

---

### Bước 2.1 — Copy cấu hình HAProxy lên VM

**Trên CMD Windows** (không phải trong SSH), chạy:
```cmd
scp ha/haproxy.cfg <tên_user>@<IP_VM_MASTER>:~/haproxy.cfg
scp ha/keepalived-master.conf <tên_user>@<IP_VM_MASTER>:~/keepalived-master.conf
scp ha/keepalived-backup.conf <tên_user>@<IP_VM_BACKUP>:~/keepalived-backup.conf
scp ha/check_haproxy.sh <tên_user>@<IP_VM_MASTER>:~/check_haproxy.sh
scp ha/check_haproxy.sh <tên_user>@<IP_VM_BACKUP>:~/check_haproxy.sh
```

---

### Bước 2.2 — Cài đặt HAProxy config (trên VM Master)

```bash
# Copy file cấu hình vào đúng vị trí
sudo cp ~/haproxy.cfg /etc/haproxy/haproxy.cfg

# Tạo thư mục runtime (chỉ cần làm 1 lần)
sudo mkdir -p /run/haproxy

# Kiểm tra cú pháp file config
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
```
> ✅ Nếu thấy `Configuration file is valid` → OK!  
> ❌ Nếu báo lỗi → kiểm tra lại IP Windows trong file config.

```bash
# Khởi động lại HAProxy
sudo systemctl restart haproxy
sudo systemctl status haproxy
```
> ✅ Trạng thái phải là `active (running)`.

---

### Bước 2.3 — Cài đặt Keepalived (trên VM Master)

```bash
# Copy script kiểm tra
sudo cp ~/check_haproxy.sh /etc/keepalived/check_haproxy.sh
sudo chmod +x /etc/keepalived/check_haproxy.sh

# Copy config Keepalived Master
sudo cp ~/keepalived-master.conf /etc/keepalived/keepalived.conf

# Khởi động Keepalived
sudo systemctl restart keepalived
sudo systemctl status keepalived
```

---

### Bước 2.4 — Cài đặt Keepalived (trên VM Backup)

SSH vào VM Backup và làm tương tự:
```bash
sudo cp ~/check_haproxy.sh /etc/keepalived/check_haproxy.sh
sudo chmod +x /etc/keepalived/check_haproxy.sh
sudo cp ~/keepalived-backup.conf /etc/keepalived/keepalived.conf
sudo systemctl restart haproxy
sudo systemctl restart keepalived
```

---

## 🧪 PHẦN 3 — TEST CÁC TÍNH NĂNG LEVEL 6

Sau khi mọi thứ đang chạy, thực hiện các bài test sau.

### ✅ Test 1 — Load Balancing Cơ Bản

Mở trình duyệt, truy cập nhiều lần:
```
http://<IP_VIP>:80
```
> `IP_VIP` mặc định là `192.168.56.100`

**Kết quả mong đợi:** Mỗi lần tải trang, thấy port xoay vòng: `8001 → 8002 → 8001 → 8002 ...`

---

### ✅ Test 2 — HAProxy Stats (Cơ chế 9: Monitoring)

Mở trình duyệt:
```
http://<IP_VM_MASTER>:8404/stats
```
Đăng nhập: **admin / admin123**

**Kết quả mong đợi:** Thấy bảng thống kê màu xanh lá, Server 1 và 2 đang `UP`, Server 3 (backup) ở trạng thái chờ.

---

### ✅ Test 3 — Dashboard Monitoring

Mở trình duyệt trên Windows:
```
http://localhost:5000
```

**Kết quả mong đợi:** Thấy dashboard hiển thị trạng thái real-time của 3 server.

---

### ✅ Test 4 — Circuit Breaker (Cơ chế 5)

Mô phỏng Server 1 bị chết:

1. Đóng cửa sổ CMD của **Server1 (port 8001)**
2. Chờ ~9 giây (HAProxy check mỗi 3s, fall=3)
3. Truy cập `http://<IP_VIP>:80` nhiều lần

**Kết quả mong đợi:** HAProxy tự động bỏ qua Server 1, chỉ dùng Server 2. Dịch vụ **không bị gián đoạn**.

4. Khởi động lại Server 1:
```cmd
python backend/app.py --port 8001
```
5. Chờ ~6 giây (rise=2, check mỗi 3s)

**Kết quả mong đợi:** Server 1 tự động được thêm lại vào pool với Slow Start (tải tăng dần 30s).

---

### ✅ Test 5 — Backup Server (Server 3)

1. Đóng **cả hai** cửa sổ Server1 và Server2
2. Chờ ~9 giây
3. Truy cập `http://<IP_VIP>:80`

**Kết quả mong đợi:** Server 3 (Backup) được kích hoạt, trang vẫn hoạt động với port `8003`.

---

### ✅ Test 6 — Rate Limiting (Cơ chế 1)

Mở file `test-ddos.html` trong trình duyệt (hoặc dùng công cụ tương tự):
- Gửi > 100 request/10 giây từ cùng 1 IP

**Kết quả mong đợi:** HAProxy trả về **HTTP 429 Too Many Requests** — IP bị chặn tạm thời.

---

### ✅ Test 7 — Priority Routing cho /stress (Cơ chế 8)

```
http://<IP_VIP>:80/stress?seconds=5
```

**Kết quả mong đợi:** Request được chuyển sang `stress_backend` (maxconn 50), các request thường ở `web_backend` (maxconn 100) vẫn không bị ảnh hưởng.

---

### ✅ Test 8 — High Availability (Failover Keepalived)

> Cần 2 người, mỗi người SSH vào 1 VM.

1. Kiểm tra VIP đang ở VM nào:
```bash
ip a | grep 192.168.56.100
```
2. Tắt HAProxy trên VM Master:
```bash
sudo systemctl stop haproxy
```
3. Chờ ~4 giây, kiểm tra lại VIP trên **VM Backup**:
```bash
ip a | grep 192.168.56.100
```

**Kết quả mong đợi:** VIP `192.168.56.100` tự động chuyển sang VM Backup. Dịch vụ **không bị gián đoạn**.

4. Khôi phục:
```bash
# Trên VM Master:
sudo systemctl start haproxy
```

---

## 🛑 PHẦN 4 — DỪNG HỆ THỐNG

### Dừng backend Windows

**Double-click `stop.bat`** hoặc:
```cmd
stop.bat
```

### Dừng HAProxy + Keepalived trên VM

```bash
sudo systemctl stop haproxy
sudo systemctl stop keepalived
```

---

## 🔍 XỬ LÝ SỰ CỐ THƯỜNG GẶP

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `http://<VIP>:80` không vào được | HAProxy chưa chạy hoặc sai IP Windows | Kiểm tra `sudo systemctl status haproxy`, sửa IP trong `haproxy.cfg` |
| Server luôn DOWN trong stats | Windows Firewall chặn port | Tắt firewall tạm hoặc mở port 8001-8003 |
| Dashboard không load được dữ liệu | Dashboard API chưa chạy hoặc sai `VM_IP` | Kiểm tra cửa sổ Dashboard API, sửa `VM_IP` trong `start.bat` |
| HAProxy báo lỗi khi start | Sai cú pháp config | Chạy `sudo haproxy -c -f /etc/haproxy/haproxy.cfg` để kiểm tra |
| VIP không chuyển sang Backup | Keepalived chưa cài hoặc cấu hình sai | Kiểm tra `sudo systemctl status keepalived` trên cả 2 VM |
| `scp` lỗi permission denied | Chưa SSH key hoặc sai username | Dùng đúng `<tên_user>` khi cài Ubuntu |

---

## 📋 CHECKLIST HOÀN THÀNH

### Windows
- [ ] `start.bat` chạy thành công, 4 cửa sổ CMD mở ra
- [ ] `localhost:8001`, `8002`, `8003` đều trả về trang web
- [ ] `localhost:5000` hiển thị Dashboard

### Ubuntu VM
- [ ] `haproxy.cfg` đã có đúng IP Windows
- [ ] `sudo haproxy -c -f /etc/haproxy/haproxy.cfg` báo `valid`
- [ ] HAProxy đang `active (running)`
- [ ] Keepalived đang `active (running)` trên cả 2 VM

### Kiểm tra Level 6
- [ ] Test 1: Load balancing xoay vòng ✅
- [ ] Test 2: Stats page hiển thị ✅
- [ ] Test 3: Dashboard monitoring ✅
- [ ] Test 4: Circuit breaker (tắt 1 server, tự recover) ✅
- [ ] Test 5: Backup server kích hoạt ✅
- [ ] Test 6: Rate limiting 429 ✅
- [ ] Test 7: Priority routing /stress ✅
- [ ] Test 8: HA Failover (VIP chuyển VM) ✅

---

> 🎉 **Hoàn thành tất cả = Level 6 PASS!**  
> Có thắc mắc thì hỏi nhóm trưởng hoặc xem thêm `ha/vm-setup.md`.
