"""
train_ppo.py — Huấn luyện AI (PPO) điều khiển HAProxy

Chạy trên Ubuntu VM (cùng máy với HAProxy + socat đã cài).
Backend Flask phải đang chạy trên Windows trước khi chạy file này.

Cài thư viện (lần đầu):
    pip install -r requirements.txt

Chạy training:
    python train_ppo.py

Kết quả: file ha_rl_trained_model.zip — bộ não AI đã huấn luyện xong.

Dùng model đã train (inference):
    python train_ppo.py --mode infer
"""

import argparse
import time
import numpy as np

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.callbacks import BaseCallback

from lb_env import HAProxyEnv

# ====== CONFIG ======
MODEL_FILE     = "ha_rl_trained_model"
TOTAL_TIMESTEPS = 10_000     # tăng lên 50_000 nếu muốn train lâu hơn
LOG_DIR        = "./ppo_logs"


# ====== CALLBACK: In tiến độ mỗi 100 bước ======

class TrainingLogger(BaseCallback):
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self._episode_rewards = []
        self._current_rewards = 0.0
        self._start_time      = time.time()

    def _on_step(self) -> bool:
        reward = self.locals.get("rewards", [0])[0]
        self._current_rewards += reward

        # Khi episode kết thúc
        dones = self.locals.get("dones", [False])
        if dones[0]:
            self._episode_rewards.append(self._current_rewards)
            self._current_rewards = 0.0

        if self.n_calls % 100 == 0:
            elapsed = time.time() - self._start_time
            avg_r   = np.mean(self._episode_rewards[-10:]) if self._episode_rewards else 0
            print(
                f"  Step {self.n_calls:6d}/{TOTAL_TIMESTEPS} | "
                f"Episodes: {len(self._episode_rewards):4d} | "
                f"Avg reward (last 10): {avg_r:+.1f} | "
                f"Elapsed: {elapsed:.0f}s"
            )
        return True


# ====== TRAINING ======

def train():
    print("="*55)
    print("=== AI Load Balancer — PPO Training ===")
    print("="*55)

    # 1. Tạo môi trường
    env = HAProxyEnv(render_mode="human")

    # 2. Kiểm tra môi trường hợp lệ (Gymnasium check)
    print("\n[1/4] Kiểm tra môi trường Gym...")
    check_env(env, warn=True)
    print("  ✅  Môi trường hợp lệ")

    # 3. Khởi tạo PPO
    print(f"\n[2/4] Khởi tạo PPO agent...")
    model = PPO(
        policy         = "MlpPolicy",       # Mạng neural MLP (phù hợp với vector obs)
        env            = env,
        learning_rate  = 3e-4,
        n_steps        = 128,               # Số bước trước khi cập nhật policy
        batch_size     = 32,
        n_epochs       = 10,
        gamma          = 0.95,              # Discount factor — coi trọng reward tương lai
        gae_lambda     = 0.95,
        clip_range     = 0.2,
        verbose        = 0,
        tensorboard_log= LOG_DIR,
    )
    print(f"  ✅  PPO sẵn sàng | Policy: MlpPolicy | timesteps: {TOTAL_TIMESTEPS:,}")

    # 4. Huấn luyện
    print(f"\n[3/4] Bắt đầu training ({TOTAL_TIMESTEPS:,} timesteps)...")
    print("      Mỗi timestep ≈ 1 giây thực → ước tính ~{:.0f} phút\n".format(
        TOTAL_TIMESTEPS / 60
    ))

    callback = TrainingLogger()
    model.learn(
        total_timesteps = TOTAL_TIMESTEPS,
        callback        = callback,
        progress_bar    = True,
    )

    # 5. Lưu model
    print(f"\n[4/4] Lưu model → {MODEL_FILE}.zip")
    model.save(MODEL_FILE)
    print(f"  ✅  Đã lưu! File: {MODEL_FILE}.zip")
    print("\n🎓 Training hoàn tất. Dùng lệnh sau để chạy inference:")
    print(f"     python train_ppo.py --mode infer")

    env.close()


# ====== INFERENCE (chạy model đã train trên production) ======

def infer():
    print("="*55)
    print("=== AI Load Balancer — Live Inference ===")
    print("="*55)
    print(f"Đang nạp model: {MODEL_FILE}.zip\n")

    env   = HAProxyEnv(render_mode="human")
    model = PPO.load(MODEL_FILE, env=env)

    obs, _ = env.reset()
    total_reward = 0.0
    step = 0

    print("AI đang điều khiển HAProxy... (Ctrl+C để dừng)\n")
    try:
        while True:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, truncated, info = env.step(int(action))
            total_reward += reward
            step += 1
            env.render()
            print(f"       reward={reward:+.1f}  total={total_reward:+.1f}")
            if done or truncated:
                print("\n[!] Episode kết thúc — reset môi trường")
                obs, _ = env.reset()
                total_reward = 0.0
    except KeyboardInterrupt:
        print("\n⏹  Dừng inference.")
    finally:
        env.close()


# ====== MAIN ======

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HAProxy RL — Train hoặc Infer")
    parser.add_argument(
        "--mode",
        choices=["train", "infer"],
        default="train",
        help="train: huấn luyện model mới | infer: chạy model đã train (mặc định: train)"
    )
    args = parser.parse_args()

    if args.mode == "train":
        train()
    else:
        infer()
