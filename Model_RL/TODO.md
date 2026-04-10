# Danh sách Công việc (TODO List) - Level 6 & 7

## Level 6 — Cascading Failure Prevention

- [x] **Nâng cấp `ha/haproxy.cfg`**
  - [x] Thêm `global` section + `stats socket /run/haproxy/admin.sock` (mở Runtime API)
  - [x] Thêm `defaults` section (timeout connect/client/server)
  - [x] `maxconn 50` per server trong backend (Cascading Failure Prevention)
  - [x] `slowstart 30s` cho từng server (phục hồi từ từ sau restart)
  - [x] ACL rules: tách `/stress` sang `stress_backend` với maxconn thấp hơn (Request Priority)
  - [x] `listen stats` port 8404 (giám sát)
- [ ] **Deploy lên Ubuntu VM và test**
  - [ ] `sudo cp ha/haproxy.cfg /etc/haproxy/haproxy.cfg`
  - [ ] `sudo systemctl restart haproxy`
  - [ ] Kiểm tra Runtime API: `echo "show stat" | sudo socat stdio /run/haproxy/admin.sock`
  - [ ] Cài socat: `sudo apt install socat`

---

## Level 7 — AI-Driven Load Balancing (RL Pipeline)

- [x] **Giai đoạn 1: Mở khóa HAProxy Runtime API** ← (làm chung với Level 6)
  - [x] `stats socket /run/haproxy/admin.sock` đã thêm vào `haproxy.cfg`

- [x] **Giai đoạn 2: Lấy dữ liệu phần cứng (Sensor)**
  - [x] Thêm `psutil` vào `backend/requirements.txt`
  - [x] Viết `backend/routes/metrics.py` → endpoint `GET /metrics` (CPU%, RAM%, Disk%)
  - [x] Đăng ký blueprint trong `backend/app.py`

- [x] **Giai đoạn 3: Viết Môi trường Giả Lập (Gym Environment)**
  - [x] `Model_RL/lb_env.py` — Class `HAProxyEnv(gym.Env)`
  - [x] Observation space 8 chiều: CPU/RAM/session/latency × 2 server
  - [x] Action space: 5 bộ weight preset (Discrete 5)
  - [x] Reward function: +10 (fast) / -50 (server DOWN) / -100 (game over)
  - [x] `_get_obs()` gọi `/metrics` từ Windows + đọc session từ HAProxy socket
  - [x] `step()` áp dụng weight → đợi 1s → tính reward

- [x] **Giai đoạn 4: Kịch bản Bắn Traffic (Locust)**
  - [x] `Model_RL/locustfile.py` — 3 loại user: NormalUser / HeavyUser / SpikeUser
  - [x] NormalUser: /health x5, /info x3, /metrics x2
  - [x] HeavyUser: /stress?seconds=1 và /stress?seconds=3

- [x] **Giai đoạn 5: Huấn luyện PPO**
  - [x] `Model_RL/train_ppo.py` — PPO với callback tiến độ + mode infer
  - [x] `Model_RL/requirements.txt` — gymnasium, stable-baselines3, psutil, locust

- [ ] **Chạy và thu thập kết quả (cần làm trên Ubuntu VM)**
  - [ ] Cài thư viện: `pip install -r Model_RL/requirements.txt`
  - [ ] Test sensor: `curl http://localhost:8001/metrics`
  - [ ] Test controller: `python Model_RL/haproxy_controller.py`
  - [ ] Test môi trường: `python Model_RL/lb_env.py`
  - [ ] Bắn traffic (terminal riêng): `locust -f Model_RL/locustfile.py --host=http://192.168.20.27 --headless -u 100 -r 10 --run-time 60s`
  - [ ] Chạy training: `python Model_RL/train_ppo.py`
  - [ ] Sau khi train: `python Model_RL/train_ppo.py --mode infer`
  - [ ] Lưu `ha_rl_trained_model.zip` để nộp đồ án
