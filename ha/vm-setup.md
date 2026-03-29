# Level 4 — Chuẩn Bị Môi Trường VM

> **Dành cho người mới** — hướng dẫn từng bước, không cần kiến thức Linux trước.
> File này chỉ hướng dẫn **cài đặt và chuẩn bị môi trường**. Cấu hình HAProxy + Keepalived sẽ làm sau.

Có **2 cách** cấu hình mạng, chọn 1 trong 2:

| | Cách 1: Bridged Adapter | Cách 2: NAT + Host-Only |
|---|---|---|
| **Độ khó** | ⭐ Đơn giản | ⭐⭐ Nhiều bước hơn |
| **Ưu điểm** | Setup nhanh, ít bước | Hoạt động trên mạng trường/công ty có bảo mật |
| **Nhược điểm** | Không hoạt động nếu mạng chặn MAC lạ | Phải cấu hình thủ công card mạng thứ 2 |
| **Dùng khi** | Mạng nhà, WiFi cá nhân | Mạng trường, công ty, WiFi yêu cầu đăng nhập |

## 📺 Video tham khảo

| Bước | Video | Thời lượng |
|---|---|---|
| Cài VirtualBox + Ubuntu Server | [Install Ubuntu Server 22.04 on VirtualBox](https://www.youtube.com/results?search_query=install+ubuntu+server+22.04+on+virtualbox+step+by+step) | ~15 phút |
| Cấu hình mạng Host-Only | [VirtualBox Host-Only Network Setup](https://www.youtube.com/results?search_query=virtualbox+host+only+adapter+network+setup+tutorial) | ~5 phút |
| Clone VM trong VirtualBox | [How to Clone a VM in VirtualBox](https://www.youtube.com/results?search_query=how+to+clone+virtual+machine+virtualbox) | ~3 phút |
| Tổng quan HAProxy + Keepalived | [HAProxy Keepalived High Availability Setup](https://www.youtube.com/results?search_query=haproxy+keepalived+high+availability+ubuntu+tutorial) | ~20 phút |

> 💡 Click vào link → YouTube sẽ hiện danh sách video liên quan, chọn video nào dễ hiểu nhất với bạn.

---

## II. QUY TRÌNH THỰC HIỆN

### BƯỚC 1: Cài đặt môi trường ảo hóa
1. Tải và cài đặt phần mềm **Oracle VM VirtualBox** từ trang chủ: https://www.virtualbox.org/wiki/Downloads
2. Tải tệp tin ảnh đĩa (ISO) của hệ điều hành **Ubuntu Server 22.04** (hoặc bản mới hơn): https://ubuntu.com/download/server

### BƯỚC 2: Tạo và cài đặt máy chủ gốc (VM1 - MASTER)
1. Mở VirtualBox, chọn **New** để tạo máy ảo mới với thông số:
   * **Name:** `LB-Master`
   * **Type:** `Linux` | **Version:** `Ubuntu (64-bit)`
   * **Memory (RAM):** `2048 MB`
   * **Hard disk:** Cấp phát động (`Dynamically allocated`), dung lượng `10 GB`.
2. Truy cập **Settings > Storage**, trỏ ổ đĩa quang ảo vào file ISO Ubuntu Server vừa tải.
3. Nhấn **Start** để khởi động và tiến hành cài đặt hệ điều hành.
   * *Lưu ý quan trọng:* Trong quá trình cài đặt, tại bước thiết lập mạng, giữ nguyên mặc định. Tại bước **SSH Setup**, bắt buộc chọn (tick) mục **Install OpenSSH server** để cho phép kết nối từ xa.
4. Hoàn tất cài đặt, khởi động lại máy ảo (Reboot), sau đó tắt máy hoàn toàn bằng lệnh: `sudo poweroff`.

### BƯỚC 3: Nhân bản máy chủ (Tạo VM2 - BACKUP)
Việc nhân bản giúp tiết kiệm thời gian thay vì cài đặt lại hệ điều hành từ đầu.
1. Đảm bảo máy `LB-Master` đang ở trạng thái tắt (Powered Off).
2. Nhấn chuột phải vào `LB-Master`, chọn **Clone...**
3. Thiết lập thông số nhân bản:
   * **Name:** `LB-Backup`
   * **MAC Address Policy:** Bắt buộc chọn **Generate new MAC addresses for all network adapters** (Tạo địa chỉ vật lý mới để tránh xung đột mạng).
4. Chọn **Full Clone** và chờ quá trình hoàn tất.

### BƯỚC 4: Cấu hình mạng — Chọn 1 trong 2 cách

---

#### 📌 CÁCH 1: Bridged Adapter (đơn giản)

> Dùng khi mạng nhà, WiFi cá nhân, không bị chặn MAC.

Làm cho **CẢ 2 MÁY ẢO**:
1. Nhấn chuột phải vào máy ảo, chọn **Settings > Network**.
2. **Adapter 1**: Đổi `Attached to` từ `NAT` sang **`Bridged Adapter`**.
3. `Name`: Chọn card mạng WiFi hoặc Ethernet đang dùng.
4. Nhấn **OK**. Khởi động (Start) cả hai máy ảo.
5. Kiểm tra IP:
   ```bash
   ip addr show
   ```
   *Tìm dòng `inet 192.168.x.x` — đó là IP của VM. 2 VM phải khác IP nhau.*

**Ví dụ IP (Cách 1):**

| Máy | IP |
|---|---|
| Windows | `192.168.1.10` (xem bằng `ipconfig`) |
| VM1 (Master) | `192.168.1.11` |
| VM2 (Backup) | `192.168.1.12` |

→ Xong Cách 1, chuyển sang **BƯỚC 5**.

---

#### 📌 CÁCH 2: NAT + Host-Only (cho mạng trường/công ty)

> Dùng khi mạng có bảo mật (chặn MAC lạ, yêu cầu đăng nhập web).
> Mô hình mạng kép:
> * **Card 1 (NAT):** Cung cấp Internet cho VM (tải gói phần mềm).
> * **Card 2 (Host-Only):** Tạo mạng LAN khép kín giữa các VM + Windows.

**Bước 4.2a: Cấu hình phần cứng mạng trên VirtualBox**

Thực hiện cho **CẢ 2 MÁY ẢO**:
1. Nhấn chuột phải vào máy ảo, chọn **Settings > Network**.
2. Tại thẻ **Adapter 1**: Đảm bảo `Attached to` đang là **NAT**.
3. Tại thẻ **Adapter 2**: 
   * Đánh dấu chọn **Enable Network Adapter**.
   * `Attached to`: Chọn **Host-only Adapter**.
   * `Name`: Chọn tên mạng hiển thị (thường là *VirtualBox Host-Only Ethernet Adapter*).
4. Nhấn **OK**. Khởi động (Start) cả hai máy ảo.

**Bước 4.2b: Cấu hình mạng trên Ubuntu**

Do Ubuntu Server không tự động nhận diện Card mạng thứ 2 (Host-Only), cần cấu hình thủ công.

**VM1 (MASTER):**
1. Đăng nhập vào máy `LB-Master`.
2. Mở tệp tin cấu hình mạng:
   ```bash
   sudo nano /etc/netplan/*.yaml
   ```
3. Bổ sung cấu hình cho card mạng `enp0s8` ngay dưới `enp0s3`. 
   *(Lưu ý: Không sử dụng phím Tab. Sử dụng phím Space/Dấu cách để căn lề thẳng hàng)*
   ```yaml
   network:
     ethernets:
       enp0s3:
         dhcp4: true
       enp0s8:
         dhcp4: true
     version: 2
   ```
4. Lưu và thoát: `Ctrl + O` → Enter → `Ctrl + X`.
5. Áp dụng cấu hình và kiểm tra:
   ```bash
   sudo netplan apply
   ip a
   ```
   *Thành công khi mục `enp0s8` xuất hiện địa chỉ IP (Ví dụ: `192.168.56.101`). Ghi lại IP này.*

**VM2 (BACKUP) — Khắc phục xung đột mạng:**

Do được nhân bản từ máy gốc, máy Backup mang theo Machine-ID cũ → tranh chấp IP với Master.

1. Đăng nhập vào máy `LB-Backup`.
2. Mở tệp cấu hình mạng:
   ```bash
   sudo nano /etc/netplan/*.yaml
   ```
3. Xóa bỏ toàn bộ các dòng chứa chữ `match` và `macaddress`. Đưa nội dung về cấu trúc tối giản y hệt VM1. Lưu và thoát.
4. Làm mới định danh máy chủ:
   ```bash
   sudo rm /etc/machine-id
   sudo systemd-machine-id-setup
   ```
5. Khởi động lại:
   ```bash
   sudo reboot
   ```
6. Đăng nhập lại, kiểm tra `ip a`. 
   *Thành công khi card `enp0s8` nhận IP mới không trùng Master (Ví dụ: `192.168.56.102`).*

**Ví dụ IP (Cách 2):**

| Máy | IP Host-Only |
|---|---|
| Windows | `192.168.56.1` (tự động có) |
| VM1 (Master) | `192.168.56.101` |
| VM2 (Backup) | `192.168.56.102` |

→ Xong Cách 2, chuyển sang **BƯỚC 5**.

---

### BƯỚC 5: Kết nối từ xa (SSH) và cài đặt phần mềm
Để thao tác thuận tiện và hỗ trợ Copy/Paste, điều khiển VM qua CMD của Windows.

1. Thu nhỏ các cửa sổ VirtualBox đang chạy.
2. Mở 2 cửa sổ **Command Prompt (CMD)** trên Windows.
3. Kết nối vào từng máy ảo:
   * Cửa sổ 1: `ssh <tên_đăng_nhập>@<IP_Máy_Master>` (Ví dụ: `ssh khoa@192.168.56.101`)
   * Cửa sổ 2: `ssh <tên_đăng_nhập>@<IP_Máy_Backup>` (Ví dụ: `ssh khoa@192.168.56.102`)
   *(Gõ `yes` nếu hệ thống hỏi xác thực, sau đó nhập mật khẩu).*
4. Cài đặt phần mềm trên **cả 2 máy**:
   ```bash
   sudo apt update
   sudo apt install -y haproxy keepalived
   ```
5. Kiểm tra cài đặt thành công:
   ```bash
   haproxy -v
   keepalived --version
   ```
   *Nếu trả về thông tin phiên bản → chuẩn bị hạ tầng hoàn tất 100%.*

---

## III. CHECKLIST HOÀN THÀNH

- [ ] VirtualBox đã cài
- [ ] VM1 (LB-Master) đã tạo, chạy Ubuntu Server
- [ ] VM2 (LB-Backup) đã clone từ VM1
- [ ] Cấu hình mạng theo Cách 1 (Bridged) hoặc Cách 2 (NAT + Host-Only)
- [ ] 2 VM có IP riêng (không trùng nhau)
- [ ] SSH từ Windows vào cả 2 VM thành công
- [ ] HAProxy đã cài trên cả 2 VM
- [ ] Keepalived đã cài trên cả 2 VM

> **Hoàn thành checklist trên = sẵn sàng làm Level 4!** 🎉
> Cấu hình HAProxy + Keepalived sẽ được viết trong các file `ha/haproxy.cfg`, `ha/keepalived-*.conf`.
