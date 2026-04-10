# Báo Cáo Thuật Toán: PPO Auto-Scaling

## 1. Lý Do Chọn PPO (Proximal Policy Optimization)
- **Tính Ổn Định (Policy Clipping):** Tránh hiện tượng đổi trạng thái đột ngột làm rơi chùm Request (Network Drop).
- **Xử lý Không gian Thực:** Hoạt động tốt hơn Q-Learning trên không gian ma trận Vector nhiều chiều (Nhiều tham số cảm biến).

## 2. Cấu Trúc Môi Trường Gym (Environment)
- **Observation Space (12 chiều):** 
  Input từ 3 Server s1, s2, s3. Tại mỗi cụm đọc 4 hệ số: `%CPU`, `%RAM`, `Sessions`, `Latency(ms)`.
- **Action Space (7 Trạng thái rời rạc):** 
  Phân bổ tổ hợp Weight (Tổng 10) để đóng ngắt 3 Server.
  - Vắng khách: `(10, 0, 0)`, `(0, 10, 0)`
  - Ngày thường: `(5, 5, 0)`, `(8, 2, 0)`, `(2, 8, 0)`
  - Đột biến tải (Spike): `(4, 4, 2)`, `(3, 3, 4)`

## 3. Hàm Mục Tiêu (Reward Function)
Agent tối đa hóa phần thưởng qua 3 mục tiêu độc lập:
1. **SLA (Độ trễ - Quan trọng nhất):** Latency < 100ms (+15). Threshold trễ > 2000ms (-50).
2. **Chi phí Vận hành (Cost):** Bật s1 hoặc s2 tốn (-2). Bật Server dự phòng s3 tốn (-5) để Agent ưu tiên đóng s3 khi tải giảm.
3. **Cascading Failure (An toàn hệ thống):** Ngăn chặn vượt giới hạn giới hạn 85% CPU. Ngưỡng trừ phạt khốc liệt (-60) để ép Load Balancer phải Scale-Out ra s3.

![Biểu đồ Huấn luyện AI](../assets/train.jpg)
