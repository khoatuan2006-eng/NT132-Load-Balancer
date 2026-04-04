# Level 7 — AI-Driven Load Balancing (Hướng dẫn Thực hành)

Thư mục này chứa toàn bộ khung sườn (skeleton code) để nâng cấp project lên tầng AI. Mục đích là huấn luyện cấu trúc Học Máy Tăng Cường (Reinforcement Learning) tự động kiểm soát sụp đổ dây chuyền cho HAProxy.

> **Đầu ra mong muốn:** Hoàn thiện code các file rỗng sao cho AI có thể quan sát (lấy Data) và tự ra tay sửa `weight` chia tải thời gian thực.

Dưới đây là nội dung nhiệm vụ cho từng file trống:

## 1. File `requirements.txt` (Khai báo Thư viện)
**Nhiệm vụ:** Khai báo cấu hình cài đặt dành cho quá trình Training AI và Load Test.
**Gợi ý cú pháp cần điền:**
- `gymnasium` (Bắt buộc - Framework tạo môi trường Game)
- `stable-baselines3` (Bắt buộc - Chứa thuật toán PPO/DQN)
- `psutil` (Để backend đọc CPU, RAM)
- `locust` (Công cụ bắn Traffic cực đại để thử server)

## 2. File `backend\routes\metrics.py` (Cung cấp Input cho AI)
**Nhiệm vụ:** Bổ sung Cảm biến (Sensor) bên phần Backend Windows để AI có thể đánh giá được Server 1, Server 2 đang chạy mệt/quá tải cỡ nào.
**Yêu cầu code:**
- Sử dụng Framework `Flask Blueprint`. Khai báo route HTTP `GET /metrics`.
- Sử dụng hàm `psutil.cpu_percent()` và `psutil.virtual_memory().percent` trả về dạng JSON.
- **Lưu ý:** Sau khi cấu hình xong file này, phải đi đến file gốc `backend\app.py` để Import Blueprint này vào.

## 3. File `haproxy_controller.py` (Phần Cổ Chai Lệnh)
**Nhiệm vụ:** Xây dựng cầu nối để code Python giao tiếp trực tiếp với cổng Unix Socket của HAProxy (Data Plane).
**Các Hàm (Functions) cần code:**
- `get_haproxy_stats()`: Trích xuất số Session hiện hành và Số lỗi kết nối từ API (hoặc bằng csv).
- `set_server_weight(server_name, weight_value)`: Bọc lệnh điều khiển vào Python (sử dụng thư viện `subprocess` hoặc HTTP POST). Cú pháp chuẩn của HAProxy: `echo "set weight app_servers/<name> <value>" | socat stdio /run/haproxy/admin.sock`.

## 4. File `lb_env.py` (Môi trường AI — Quan trọng nhất)
**Nhiệm vụ:** Bọc HAProxy lại thành một trò chơi điện tử để AI điều khiển.
**Cấu trúc cần code:** Kế thừa Class `gym.Env` của thư viện Gymnasium.
- `__init__(self)`: Phải cấu hình không gian hành động `action_space` (Dải trọng số Weight từ 0-256) và không gian quan sát `observation_space`.
- `_get_obs(self)`: Hàm này sẽ tự động gọi HTTP `/metrics` bên Windows và lấy stats bên HAProxy Controller ghép thành 1 Vector [1D].
- `step(self, action)`: Trái tim của AI. Nhận lệnh từ con Bot, gọi file Controller để cập nhật HAProxy. Sau 1 giây, tính toán **Điểm Thưởng (Reward)**: Ví dụ: Nếu độ trễ phản hồi bé hơn 50ms (+10 điểm), nếu có dính lỗi HTTP 503 Cascading Failure (-100 điểm, Game Over).

## 5. File `locustfile.py` (Tấn công mô phỏng)
**Nhiệm vụ:** Viết kịch bản người dùng đấm dồn dập vào HAProxy.
**Gợi ý:** Viết một Class `WebsiteUser(HttpUser)` có hàm `wait_time` ngẫu nhiên. Tạo `@task` truy xuất liên tiếp vào `/health` (truy cập nhẹ) và thỉnh thoảng giã vào `/stress` (truy cập rất nặng).

## 6. File `train_ppo.py` (Quá trình Huấn luyện)
**Nhiệm vụ:** Triệu hồi Neural Network và dạy nó tối giản hóa độ trễ máy chủ.
**Yêu cầu code:**
- Import thư viện `PPO` từ `stable_baselines3`.
- Khởi tạo môi trường: `env = HAProxyEnv()`.
- Chạy huấn luyện: `model.learn(total_timesteps=10000)`.
- Kết xuất: `model.save("ha_rl_trained_model")` — File zip này sẽ đem đi bảo vệ đồ án!

---
> 🌟 **Lời khuyên làm việc nhóm:** Đừng dàn trải ra code một lúc, hãy lần lượt code và Test theo thứ tự: Metric 👉 Controller 👉 Locust 👉 Env 👉 Train PPO.
