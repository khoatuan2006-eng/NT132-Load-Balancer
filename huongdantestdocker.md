# Hướng Dẫn Kịch Bản Test Hệ Thống Load Balancer với Docker (Level 5 - 6)

Tài liệu này hướng dẫn chi tiết các bước để các thành viên trong nhóm kiểm tra hệ thống Load Balancer đã được đóng gói Docker hoàn chỉnh, bao gồm HAProxy và các Backend Server (Flask).

## 1. Khởi động hệ thống

Để bắt đầu, mở terminal (viết lệnh) tại thư mục chứa file `docker-compose.yml` (thư mục `NT132-Load-Balancer`) và chạy lệnh sau để build và khởi động tất cả container ở chế độ chạy nền (detached mode):

```bash
docker-compose up -d --build
```

Kiểm tra trạng thái các container để đảm bảo tất cả đều đang chạy (Up) và khỏe mạnh (healthy):

```bash
docker-compose ps
```

Các container sẽ có tên là: `haproxy1`, `haproxy2`, `server1`, `server2`, `server3`.

## 2. Truy cập Giao diện Giám sát HAProxy (Stats Page)

Dự án này sử dụng 2 Load Balancer HAProxy. Bạn có thể mở giao diện bằng trình duyệt:
- **HAProxy 1 (Master):** [http://localhost:18404/stats](http://localhost:18404/stats)
- **HAProxy 2 (Backup):** [http://localhost:18405/stats](http://localhost:18405/stats)

**Thông tin đăng nhập:**
- **User:** `admin`
- **Password:** `admin123`

*Hãy quan sát trạng thái của các backend server. Bạn sẽ thấy `s1`, `s2`, `s3` có màu xanh lá (UP) trong cả 2 dashboard. Tức là các server backend đã sẵn sàng.*

---

## 3. Kịch bản Test 1: Tính năng Load Balancing cơ bản (Roundrobin)

Chúngạm sẽ gửi các request đến HAProxy để kiểm tra thuật toán chia tải. Mở terminal mới và sử dụng `curl` liên tục vài lần:

**Gửi request đến HAProxy Master (Port 18080):**
```bash
curl http://localhost:18080/info
```

**Kết quả mong đợi:** 
Phản hồi nhận được sẽ hiển thị nội dung chứa Server IP (hoặc Server hostname/ID) thay đổi tuần tự: từ `server1`, qua `server2`, rồi qua `server3`. Điều này chứng tỏ chia tải Roundrobin đang hoạt động đúng.

---

## 4. Kịch bản Test 2: Tính sẵn sàng cao (High Availability) & Failover

Kiểm tra hệ thống vẫn hoạt động bảo vệ người dùng, ngay cả khi một server backend bị lỗi mạng hoặc bị sập đột ngột.

**Bước 1:** Dừng `server1`. Chạy lệnh trong terminal:
```bash
docker-compose stop server1
```

**Bước 2:** Refresh và kiểm tra bảng điều khiển HAProxy Stats ([http://localhost:18404/stats](http://localhost:18404/stats)). Sau khoảng vài giây, do cơ chế liên tục healthcheck thất bại, `s1` sẽ chuyển trạng thái sang đỏ (DOWN).

**Bước 3:** Tiếp tục gửi request tới HAProxy:
```bash
curl http://localhost:18080/info
```
**Kết quả mong đợi:** Bạn sẽ thấy các phản hồi trả về thành công đều đặn và chỉ được phục vụ bởi `server2` và `server3`. HAProxy đã khoanh vùng và cách ly `server1` ra khỏi hệ thống mạng chia tải. Người dùng hoàn toàn không cảm nhận được "sự chết" của server 1.

**Bước 4:** Phục hồi `server1`:
```bash
docker-compose start server1
```
Quan sát trên Stats UI, khoảng 15 giây sau khi container start lại xong, healthcheck từ HAProxy sẽ thành công, nó cập nhật sang màu xanh (UP). Dòng tải request mới sẽ tự động được rẽ đều ngược vào cho `server1` thông qua cơ chế `slowstart`.

---

## 5. Kịch bản Test 3: Cascading Failure Protection (Cơ chế bảo vệ bằng Maxconn & Priority)

Đảm bảo tránh tính trạng hiệu ứng sập dây chuyền cục bộ (Cascading Failure), bảo vệ các request thiết yếu trên endpoint `/info` khi có tác nhân tạo tải nặng vào endpoint ưu tiên thấp `/stress`.

Hệ thống HAProxy lúc này đã được quy định:
- Request ưu tiên cao, nhẹ (`/info`, `/health`): Max kết nối lên backend là `50`.
- Request ưu tiên thấp, nặng hệ thống CPU (`/stress`): Max kết nối hàng đợi là `10`.

Để test phần này, mỗi bạn cần cài một tool test tải trên máy, ví dụ dùng **Apache Benchmark** (`ab`).
*Tải Apache Benchmark trên Windows: Bằng việc lấy các file tải từ apache bundle, hoặc dùng JMeter.*

**Mô phỏng tình huống ngập luồng:**
Mở 2 terminal.
1. Tại Terminal 1, dùng ab để spam lưu lượng mạnh mẽ vượt giới hạn (ví dụ spam 500 request, 50 request mở cùng lúc - `concurrency`) nhắm vào /stress:
```bash
ab -n 500 -c 50 http://localhost:18080/stress
```

2. Ngay trong lúc Terminal 1 đang chạy, sang Terminal 2 gửi request xem thông tin web bình thường:
```bash
curl http://localhost:18080/info
```

**Kết quả đánh giá:** 
- Rất nhiều các công việc bên luồng ở Terminal 1 có thể trễ (timeout), hoặc nhận về HTTP Status Code như `503 Service Unavailable`, lúc ấy giới hạn số lượng (`maxconn 10`) giúp Backend Server Flask không bị quá tải CPU/RAM đến sập máy (`OOM Killed`).
- Bạn sẽ thấy bên phía Terminal 2, lệnh `curl` gửi vào `/info` vẫn phản hồi nhanh bình thường mà không bị khựng lại hay chết theo, do HAProxy đảm bảo luồng ưu tiên này được đi đường Backend khoẻ mạnh. Hiệu ứng sập lan đã được khắc phục hoàn toàn.

---

## 6. Dọn dẹp hệ thống sau khi test

Khi hoàn thành các bước kiểm tra, tắt ứng dụng bằng cách gỡ bỏ các container khỏi Docker Engine và thu gọn network:

```bash
docker-compose down
```
*(Option: Nếu có chỉnh sửa Config ha/haproxy.cfg, cần phải start lại từ lệnh đầu để lấy file cfg mới nhất vào container).*
