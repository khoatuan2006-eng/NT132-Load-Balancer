"""
lb_env.py — Môi trường Gymnasium (Bản Pro - Auto Scaling)

Biến HAProxy thành 1 "Đám Mây" để AI học điều chỉnh weight cho 3 Server.
- STATE (12D): CPU, RAM, Session, Latency của s1, s2, s3.
- ACTION (7D): Các tổ hợp cho Ngày, Đêm, và Khẩn cấp.
- REWARD (Ultimate): SLA + Năng lượng + An toàn.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import requests
import time

from haproxy_controller import (
    get_server_stats, get_session_count, get_response_time, get_server_status, set_server_weight
)

WINDOWS_IP   = "192.168.56.1"
BACKEND_URLS = {
    "s1": f"http://{WINDOWS_IP}:8001",
    "s2": f"http://{WINDOWS_IP}:8002",
    "s3": f"http://{WINDOWS_IP}:8003",
}
METRICS_TIMEOUT = 2
STEP_INTERVAL   = 1

# Không gian Hành động — Tính theo tổng 10 point để dễ quan sát
WEIGHT_ACTIONS = [
    (10, 0, 0), # 0: Đêm (Ngủ đông s2, s3)
    (0, 10, 0), # 1: Đêm (Đổi s1 nghỉ để s1 bảo trì)
    (5, 5, 0),  # 2: Ngày bình thường (Cân bằng s1, s2)
    (8, 2, 0),  # 3: Ngày lệch chuẩn (s1 gánh chính)
    (2, 8, 0),  # 4: Ngày lệch chuẩn (s2 gánh chính)
    (4, 4, 2),  # 5: Khẩn cấp cấp 1 (Bật s3 hỗ trợ nhẹ)
    (3, 3, 4),  # 6: Khẩn cấp cấp 2 (Thiệt hại lan rộng, s3 gánh ngang ngửa)
]

def _get_metrics(server_url: str) -> dict:
    try:
        r = requests.get(f"{server_url}/metrics", timeout=METRICS_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            return {"cpu": float(data.get("cpu_percent", 100.)), "ram": float(data.get("ram_percent", 100.))}
    except Exception: pass
    return {"cpu": 100.0, "ram": 100.0}

def _measure_latency(server_url: str) -> float:
    try:
        start = time.time()
        r = requests.get(f"{server_url}/health", timeout=METRICS_TIMEOUT)
        if r.status_code == 200: return (time.time() - start) * 1000
    except Exception: pass
    return 9999.0

class HAProxyEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, render_mode=None):
        super().__init__()
        self.render_mode = render_mode
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(12,), dtype=np.float32)
        self.action_space = spaces.Discrete(len(WEIGHT_ACTIONS))
        self._step_count   = 0
        self._last_action  = 0 # Khởi động ban đêm (10, 0, 0)
        self._last_cpu = [0, 0, 0]

    def _get_obs(self) -> np.ndarray:
        m1, m2, m3 = _get_metrics(BACKEND_URLS["s1"]), _get_metrics(BACKEND_URLS["s2"]), _get_metrics(BACKEND_URLS["s3"])
        lat1, lat2, lat3 = _measure_latency(BACKEND_URLS["s1"]), _measure_latency(BACKEND_URLS["s2"]), _measure_latency(BACKEND_URLS["s3"])
        sess1, sess2, sess3 = get_session_count("s1"), get_session_count("s2"), get_session_count("s3")
        
        # Cập nhật _last_cpu
        self._last_cpu = [m1["cpu"], m2["cpu"], m3["cpu"]]

        obs = np.array([
            m1["cpu"]/100., m1["ram"]/100., min(max(sess1,0),50)/50., min(lat1,2000.)/2000.,
            m2["cpu"]/100., m2["ram"]/100., min(max(sess2,0),50)/50., min(lat2,2000.)/2000.,
            m3["cpu"]/100., m3["ram"]/100., min(max(sess3,0),50)/50., min(lat3,2000.)/2000.,
        ], dtype=np.float32)
        return obs

    def _compute_reward(self, obs: np.ndarray, action: int) -> tuple[float, bool]:
        stats = {
            "s1": {"cpu": obs[0]*100, "lat": obs[3]*2000, "w": WEIGHT_ACTIONS[action][0]},
            "s2": {"cpu": obs[4]*100, "lat": obs[7]*2000, "w": WEIGHT_ACTIONS[action][1]},
            "s3": {"cpu": obs[8]*100, "lat": obs[11]*2000, "w": WEIGHT_ACTIONS[action][2]}
        }
        
        # Lọc ra các server đang hoạt động
        active_srvs = [v for k, v in stats.items() if v["w"] > 0]
        
        if not active_srvs:
            return -200, True # Lỗi logic
            
        max_lat = max([srv["lat"] for srv in active_srvs])
        max_cpu = max([srv["cpu"] for srv in active_srvs])

        reward = 0.0
        
        # 1. DOANH THU (Service Level Agreement - Tốc độ)
        if max_lat > 2000: reward -= 50; done = True # Bị lỗi TimeOut
        else: done = False

        if max_lat < 100: reward += 15
        elif max_lat < 300: reward += 5
        elif max_lat < 800: reward -= 5
        else: reward -= 20

        # 2. CHI PHÍ KHỞI ĐỘNG (Energy/Operating Cost)
        cost = 0
        if stats["s1"]["w"] > 0: cost -= 2
        if stats["s2"]["w"] > 0: cost -= 2
        if stats["s3"]["w"] > 0: cost -= 5 # s3 là dự phòng, mở lên cực đắt
        reward += cost

        # 3. AN TOÀN CPU MÁY CHỦ (Phòng chống Cascading Failure)
        if max_cpu > 85: reward -= 60
        elif max_cpu > 70: reward -= 15
        elif max_cpu < 50: reward += 5

        # 4. CHÊNH LỆCH CÂN BẰNG TẢI (Fairness)
        if len(active_srvs) >= 2:
            cpu_diff = max_cpu - min([srv["cpu"] for srv in active_srvs])
            if cpu_diff > 30: reward -= 3

        # 5. ỔN ĐỊNH HỆ THỐNG (Anti-Ping-Pong Mode)
        if action != self._last_action:
            reward -= 0.5

        return reward, done

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._step_count = 0
        self._last_action = 0
        set_server_weight("s1", 10)
        set_server_weight("s2", 0)
        set_server_weight("s3", 0)
        return self._get_obs(), {}

    def step(self, action: int):
        w1, w2, w3 = WEIGHT_ACTIONS[action]
        set_server_weight("s1", w1)
        set_server_weight("s2", w2)
        set_server_weight("s3", w3)
        time.sleep(STEP_INTERVAL)

        obs = self._get_obs()
        reward, done = self._compute_reward(obs, action)
        self._last_action = action
        self._step_count += 1
        truncated = self._step_count >= 200

        info = {
            "w": (w1, w2, w3),
            "cpu": (obs[0]*100, obs[4]*100, obs[8]*100),
            "lat": (obs[3]*2000, obs[7]*2000, obs[11]*2000),
            "reward": reward
        }
        return obs, reward, done, truncated, info

    def render(self):
        if self.render_mode == "human":
            w = WEIGHT_ACTIONS[self._last_action]
            obs = self._get_obs()
            print(
                f"Step {self._step_count:3d} | W({w[0]},{w[1]},{w[2]}) | "
                f"S1(CPU:{obs[0]*100:3.0f}%, {obs[3]*2000:4.0f}ms) "
                f"S2(CPU:{obs[4]*100:3.0f}%, {obs[7]*2000:4.0f}ms) "
                f"S3(CPU:{obs[8]*100:3.0f}%, {obs[11]*2000:4.0f}ms) "
            )

if __name__ == "__main__":
    env = HAProxyEnv(render_mode="human")
    obs, _ = env.reset()
    for _ in range(5):
        obs, reward, done, tr, _ = env.step(env.action_space.sample())
        env.render()
        print(f"Reward: {reward:.1f}")
        if done: break
