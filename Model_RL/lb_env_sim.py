"""
lb_env_sim.py — Môi trường Giả lập Toán học (To run in Colab/Local without Real Servers)

- Không cần kết nối tới HAProxy thật. Không cần Flask.
- Sử dụng mô hình mô phỏng hàng đợi (M/M/1 Queue) để tính toán CPU và Latency.
- Chạy siêu nhanh, phù hợp cho Training số lượng lớn (100,000 steps).
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import math

class HAProxySimEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, max_steps=200):
        super().__init__()
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(12,), dtype=np.float32)
        
        # 7 Hành động (Actions) cho 3 Server
        self.WEIGHT_ACTIONS = [
            (10, 0, 0), # Đêm
            (0, 10, 0), # Đêm
            (5, 5, 0),  # Ngày
            (8, 2, 0),  # Lệch 1
            (2, 8, 0),  # Lệch 2
            (4, 4, 2),  # Cấp cứu 1 (s3 gánh 20%)
            (3, 3, 4),  # Cấp cứu 2 (Thiệt hại nặng)
        ]
        self.action_space = spaces.Discrete(len(self.WEIGHT_ACTIONS))
        self.max_steps = max_steps
        self.reset()
        
    def _simulate_traffic(self, time_step):
        # Mô phỏng sóng Sine (như Locust Day/Night)
        base_traffic = 50 + 40 * math.sin(time_step * (2 * math.pi / 60))
        # Khủng hoảng (Spike) ngẫu nhiên mỗi 45s
        if time_step % 45 > 40:
            return base_traffic + 100
        return max(10, base_traffic)

    def _math_model(self, incoming_reqs, weight):
        # Hệ số sức mạnh server (S1, S2 mạnh, S3 yếu hơn tí)
        capacity = 100 # Requests/s tối đa 1 server gánh 100%
        
        # Traffic vào server này dựa theo Weight
        # Weight tổng luôn là 10.
        handled_reqs = incoming_reqs * (weight / 10.0)
        
        if weight == 0:
            return 0.0, 10.0, 0 # CPU 0, lat 10ms, 0 reqs
            
        cpu = min(100.0, (handled_reqs / capacity) * 100)
        
        # Latency (Hàm phi tuyến tính, CPU > 80% thì lat tăng cực gắt)
        if cpu < 50: lat = 20 + cpu
        elif cpu < 80: lat = 20 + cpu * 1.5
        elif cpu < 95: lat = 100 + (cpu - 80) * 20
        else: lat = 800 + (cpu - 95) * 100
        
        return cpu, min(2000.0, lat), min(50, handled_reqs)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.step_count = 0
        self.last_action = 0
        return self._get_obs(10, 0, 0), {}

    def _get_obs(self, w1, w2, w3):
        traffic = self._simulate_traffic(self.step_count)
        
        c1, l1, _ = self._math_model(traffic, w1)
        c2, l2, _ = self._math_model(traffic, w2)
        c3, l3, _ = self._math_model(traffic, w3)
        
        # Lưu lại state để tính reward
        self.current_state = {"c1":c1, "l1":l1, "w1":w1, 
                              "c2":c2, "l2":l2, "w2":w2, 
                              "c3":c3, "l3":l3, "w3":w3}
        
        obs = np.array([
            c1/100., 0.5, 0.5, l1/2000.,
            c2/100., 0.5, 0.5, l2/2000.,
            c3/100., 0.5, 0.5, l3/2000.,
        ], dtype=np.float32)
        return obs

    def step(self, action):
        w1, w2, w3 = self.WEIGHT_ACTIONS[action]
        obs = self._get_obs(w1, w2, w3)
        
        stats = [
            {"cpu": self.current_state["c1"], "lat": self.current_state["l1"], "w": w1},
            {"cpu": self.current_state["c2"], "lat": self.current_state["l2"], "w": w2},
            {"cpu": self.current_state["c3"], "lat": self.current_state["l3"], "w": w3}
        ]
        active_srvs = [s for s in stats if s["w"] > 0]
        
        if not active_srvs:
            return obs, -200, True, False, {}
            
        max_lat = max([s["lat"] for s in active_srvs])
        max_cpu = max([s["cpu"] for s in active_srvs])

        reward = 0.0
        
        # 1. DOANH THU (SLA)
        if max_lat > 2000: reward -= 50; done = True
        else: done = False

        if max_lat < 100: reward += 15
        elif max_lat < 300: reward += 5
        elif max_lat < 800: reward -= 5
        else: reward -= 20

        # 2. CHI PHÍ (Energy)
        if w1 > 0: reward -= 2
        if w2 > 0: reward -= 2
        if w3 > 0: reward -= 5

        # 3. AN TOÀN CPU
        if max_cpu > 85: reward -= 30
        elif max_cpu > 70: reward -= 10
        elif max_cpu < 50: reward += 5

        # 4. CÂN BẰNG TẢI
        if len(active_srvs) >= 2:
            cpu_diff = max_cpu - min([srv["cpu"] for srv in active_srvs])
            if cpu_diff > 20: reward -= 3

        # 5. ỔN ĐỊNH
        if action != self.last_action:
            reward -= 2

        self.last_action = action
        self.step_count += 1
        truncated = self.step_count >= self.max_steps
        
        info = {"traffic": self._simulate_traffic(self.step_count), "reward": reward}
        return obs, reward, done, truncated, info
