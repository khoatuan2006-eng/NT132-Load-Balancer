# Level 4 — Chuẩn Bị Môi Trường VM

> **Dành cho người mới** — hướng dẫn từng bước, không cần kiến thức Linux trước.
> File này chỉ hướng dẫn **cài đặt và chuẩn bị môi trường**. Cấu hình HAProxy + Keepalived sẽ làm sau.

## 📺 Video tham khảo

| Bước | Video | Thời lượng |
|---|---|---|
| Cài VirtualBox + Ubuntu Server | [Install Ubuntu Server 22.04 on VirtualBox](https://www.youtube.com/results?search_query=install+ubuntu+server+22.04+on+virtualbox+step+by+step) | ~15 phút |
| Cấu hình mạng Bridge | [VirtualBox Bridged Network Setup](https://www.youtube.com/results?search_query=virtualbox+bridged+adapter+network+setup+tutorial) | ~5 phút |
| Clone VM trong VirtualBox | [How to Clone a VM in VirtualBox](https://www.youtube.com/results?search_query=how+to+clone+virtual+machine+virtualbox) | ~3 phút |
| Tổng quan HAProxy + Keepalived | [HAProxy Keepalived High Availability Setup](https://www.youtube.com/results?search_query=haproxy+keepalived+high+availability+ubuntu+tutorial) | ~20 phút |

> 💡 Click vào link → YouTube sẽ hiện danh sách video liên quan, chọn video nào dễ hiểu nhất với bạn.

---

## Bước 1: Cài VirtualBox

Mở **Start Menu** → tìm **"Oracle VM VirtualBox"** → nếu có thì đã cài, bỏ qua bước này.

Nếu chưa cài:
1. Tải tại: https://www.virtualbox.org/wiki/Downloads
2. Chọn **Windows hosts**
3. Cài đặt bình thường (Next → Next → Install)

---

## Bước 2: Tạo 2 VM Ubuntu

### 2.1 Tạo VM1 (MASTER)

> Nếu đã có VM Ubuntu (ví dụ từ môn khác), có thể **Clone** luôn ở bước 2.2, không cần tạo mới.

**Tạo mới (nếu chưa có VM nào):**

1. Tải **Ubuntu Server 22.04 ISO**: https://ubuntu.com/download/server (~2GB)
2. Mở **VirtualBox** → bấm **New**
3. Điền:
   - Name: `LB-Master`
   - Type: `Linux`
   - Version: `Ubuntu (64-bit)`
4. **Memory**: `2048 MB` (2GB là đủ)
5. **Hard disk**: `Create a virtual hard disk now` → VDI → Dynamically allocated → `10 GB`
6. Bấm **Create**

**Cài Ubuntu Server vào VM:**
1. Chọn VM → **Settings** → **Storage** → click ổ đĩa trống → chọn file ISO
2. Bấm **Start** để boot VM
3. Làm theo hướng dẫn cài Ubuntu:
   - Ngôn ngữ: **English**
   - Chọn **Ubuntu Server** (không phải minimized)
   - Cấu hình mạng: để mặc định
   - Tạo user: nhập username và password (ví dụ: `user` / `123456`)
   - **Tick cài OpenSSH server** ← quan trọng, để SSH từ Windows vào
   - Đợi cài xong → **Reboot**

### 2.2 Tạo VM2 (BACKUP) — Clone từ VM1

> **Clone** = copy nguyên VM1, không cần cài lại Ubuntu từ đầu.

1. **Tắt VM1** trước (Right-click → Close → Power Off)
2. Right-click VM1 → **Clone...**
3. Điền:
   - Name: `LB-Backup`
   - MAC Address Policy: **Generate new MAC addresses for all network adapters**
4. Clone type: **Full Clone**
5. Bấm **Clone** → đợi vài phút

---

## Bước 3: Cấu hình mạng (QUAN TRỌNG!)

> Bước này quyết định 2 VM có nói chuyện được với nhau và với máy Windows không.

### 3.1 Đổi network adapter sang Bridge

Làm cho **cả 2 VM**:

1. Chọn VM → **Settings** → **Network**
2. **Adapter 1**:
   - Attached to: đổi từ `NAT` sang **`Bridged Adapter`**
   - Name: chọn **card mạng WiFi hoặc Ethernet** đang dùng
   - Bấm **OK**

> **Bridge Adapter** = VM nhận IP cùng mạng LAN với máy Windows → tất cả nói chuyện được.

### 3.2 Khởi động và kiểm tra IP

1. **Start cả 2 VM**, đăng nhập
2. Xem IP:

```bash
ip addr show
```

Tìm dòng `inet 192.168.x.x` — đó là IP của VM.

**Ví dụ:**

| Máy | IP |
|---|---|
| Máy Windows | `192.168.1.10` (xem bằng `ipconfig` trên CMD) |
| VM1 (Master) | `192.168.1.11` |
| VM2 (Backup) | `192.168.1.12` |

### 3.3 Test kết nối

Từ **VM1**:
```bash
ping 192.168.1.12    # ping VM2
ping 192.168.1.10    # ping máy Windows
```

Từ **máy Windows** (CMD):
```cmd
ping 192.168.1.11    # ping VM1
```

> ⚠️ Nếu ping không được: kiểm tra lại Bridged Adapter và tắt Windows Firewall tạm thời.

---

## Bước 4: Cài HAProxy + Keepalived

Đăng nhập vào **từng VM** và chạy:

```bash
# Cập nhật package
sudo apt update

# Cài HAProxy + Keepalived
sudo apt install -y haproxy keepalived

# Kiểm tra cài thành công
haproxy -v
keepalived --version
```

Nếu thấy version number → **cài thành công** ✅

---

## Checklist hoàn thành

- [ ] VirtualBox đã cài
- [ ] VM1 (Master) đã tạo, chạy Ubuntu
- [ ] VM2 (Backup) đã clone từ VM1
- [ ] Cả 2 VM dùng **Bridged Adapter**
- [ ] 2 VM ping được nhau
- [ ] VM ping được máy Windows (và ngược lại)
- [ ] HAProxy đã cài trên cả 2 VM
- [ ] Keepalived đã cài trên cả 2 VM

> **Hoàn thành checklist trên = sẵn sàng làm Level 4!** 🎉
> Cấu hình HAProxy + Keepalived sẽ được viết trong các file `ha/haproxy.cfg`, `ha/keepalived-*.conf`.
