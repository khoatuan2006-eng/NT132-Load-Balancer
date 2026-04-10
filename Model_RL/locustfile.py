"""
locustfile.py — Kịch bản bắn traffic kết hợp Bùng Nổ theo Chu kỳ (Sine Wave)

Mô phỏng chu kỳ Ngày/Đêm và các đợt Sale (Spikes) để ép AI học cách Auto-Scaling (Tắt/Bật máy).
"""

from locust import HttpUser, task, between, events, LoadTestShape
import math

class NormalUser(HttpUser):
    weight    = 8
    wait_time = between(0.5, 2.0)

    @task(5)
    def check_health(self):
        with self.client.get("/health", catch_response=True) as resp:
            if resp.status_code == 200: resp.success()
            else: resp.failure("503")

    @task(3)
    def get_info(self):
        self.client.get("/info")

    @task(2)
    def get_metrics(self):
        self.client.get("/metrics")

class HeavyUser(HttpUser):
    weight    = 2
    wait_time = between(0.1, 0.5)

    @task
    def stress_light(self):
        with self.client.get("/stress?seconds=1", catch_response=True, timeout=5) as resp:
            if resp.status_code == 503: resp.failure("503")

class DayNightShape(LoadTestShape):
    """
    Biến đổi lượng User theo hàm hình Sin. 
    Chu kỳ: 60 giây.
    Mức thấp nhất (Đêm) = 15 user. Mức cao nhất (Ngày) = 100 user.
    Thi thoảng có các gai nhọn (Sale) = 150 user.
    """
    time_limit = 600
    spawn_rate = 20

    def tick(self):
        run_time = self.get_run_time()
        if run_time > self.time_limit:
            return None

        # Sóng cơ sở (Chu kỳ 60s)
        base_users = 50 + 40 * math.sin(run_time * (2 * math.pi / 60))
        
        # Thêm các đợt bùng nổ (Spike) ngẫu nhiên mỗi 45s (Kéo dài 5s)
        if run_time % 45 > 40:
            target_users = base_users + 100 # Bùng nổ thêm 100 user
        else:
            target_users = base_users

        target_users = max(10, int(target_users)) # Không bao giờ dưới 10 user ban đêm
        return (target_users, self.spawn_rate)

@events.quitting.add_listener
def on_quit(environment, **kwargs):
    stats = environment.stats.total
    print("\n" + "="*50)
    print("=== KẾT QUẢ LOAD TEST (AUTO-SCALING SCENARIO) ===")
    print(f"  Tổng request    : {stats.num_requests}")
    print(f"  Thất bại        : {stats.num_failures} ({100*stats.fail_ratio:.1f}%)")
    print(f"  Response trung bình : {stats.avg_response_time:.0f}ms")
    print("="*50)
