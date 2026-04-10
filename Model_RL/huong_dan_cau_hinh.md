# Hướng Dẫn Cấu Hình Hệ Thống AI Load Balancer

## 1. Yêu Cầu Môi Trường
- **Windows:** Chạy bộ mã nguồn Backend (IP Host-Only `192.168.56.1`).
- **Máy ảo Ubuntu:** Cài đặt HAProxy, Python 3 và socat (IP `192.168.56.101`).

## 2. Cấu Hình HAProxy
Trên **Terminal Ubuntu**, khởi tạo các gói dịch vụ cơ bản và cập nhật cấu hình:
```bash
sudo apt update
sudo apt install haproxy socat -y

# Đẩy cấu hình mới từ project lên /etc/
sudo cp ~/haproxy.cfg /etc/haproxy/haproxy.cfg
sudo systemctl restart haproxy
```

## 3. Cấu Hình Component AI (PPO)
Để tối ưu không gian đĩa trên Ubuntu, cài đặt môi trường ảo (venv) chạy PyTorch CPU-Only:
```bash
sudo apt install python3.13-venv -y
python3 -m venv ~/ml_venv
source ~/ml_venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install stable-baselines3 numpy gymnasium psutil locust requests
```

## 4. Quá Trình Khởi Động
Thực hiện chạy 3 công đoạn để khởi động Load Balancer AI:

**Bước 1: Backend (Windows)** 
Mở CMD/PowerShell tại Window và khởi động Flask:
```powershell
.\start.bat
```

**Bước 2: AI Control Agent (Ubuntu)** 
Kích hoạt Vận hành Suy luận (Inference). Mở cửa sổ SSH Ubuntu thứ 1:
```bash
cd ~/Model_RL
source ~/ml_venv/bin/activate
python3 train_ppo.py --mode infer
```

**Bước 3: Stress Testing (Ubuntu/Windows)** 
Kiểm thử Load Balancing. Mở cửa sổ SSH Terminal thứ 2, chạy Locust:
```bash
cd ~/Model_RL
source ~/ml_venv/bin/activate
locust -f locustfile.py --host=http://192.168.56.101 --headless -u 200 -r 50 --run-time 60s
```
