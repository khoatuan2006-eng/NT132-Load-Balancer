# Danh sách Công việc (TODO List) - Level 7 AI Load Balancing

Dưới đây là các đầu việc chi tiết để biến HAProxy từ tĩnh thành một cỗ máy biết tự học (RL - Reinforcement Learning). 
Ghi chú: *File này chỉ để theo dõi tiến độ công việc.*

- [ ] **Giai đoạn 1: Mở khóa HAProxy Runtime API**
  - [ ] Chỉnh sửa `ha/haproxy.cfg` để mở cổng Unix Socket (`/run/haproxy/admin.sock`).
  - [ ] Cài đặt công cụ `socat` trên máy ảo Ubuntu để gửi lệnh vào Socket.

- [ ] **Giai đoạn 2: Lấy dữ liệu phần cứng (Sensor)**
  - [ ] Thêm thư viện `psutil` vào file `requirements.txt` của Backend Windows.
  - [ ] Dùng thư viện `psutil` viết code ở `backend\routes\metrics.py` để lấy ra % CPU và RAM (Giao cho con AI đọc để biết server đang ngộp hay thảnh thơi).
  - [ ] Sửa file gốc `backend\app.py` để mở đường dẫn (route) `/metrics` này ra ngoài.

- [ ] **Giai đoạn 3: Viết Môi trường Giả Lập (Gym Environment)**
  - [ ] Bật file rỗng `level7_rl\lb_env.py` để code Class bọc HAProxy thành 1 Game (kế thừa `gym.Env`).
  - [ ] Code hàm thu thập thông tin State (`_get_obs()`): Lấy số liệu CPU từ API Windows; Lấy active session từ Socket HAProxy.
  - [ ] Code hàm hành động Action (`step()`): Ánh xạ mảng Action của máy AI thành lệnh Bash sửa thông số `weight`, và trả về Điểm Thưởng (Reward) nếu độ trễ thấp.

- [ ] **Giai đoạn 4: Kịch bản Bắn Traffic (Locust)**
  - [ ] Sử dụng công cụ `locust` viết code trong `level7_rl\locustfile.py` để bắn rác vào `/stress` liên tục nhằm ép chết server (Chaos Engineering).

- [ ] **Giai đoạn 5: Sinh Não AI (Huấn luyện PPO)**
  - [ ] Cài thư viện `stable-baselines3`, code file `train_ppo.py` chèn thuật toán PPO.
  - [ ] Chạy lệnh `model.learn(total_timesteps=10000)` qua đêm để AI tự sửa lỗi, tự tối giản độ trễ.
  - [ ] Xuất ra sản phẩm cuối cùng `rl_model.zip` (Bộ não chốt) để nộp chung với đồ án.
