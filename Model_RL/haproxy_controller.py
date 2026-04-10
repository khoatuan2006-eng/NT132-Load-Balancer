"""
haproxy_controller.py — Cầu nối Python ↔ HAProxy Runtime API

Chạy trên Ubuntu VM (cùng máy với HAProxy).
Giao tiếp qua Unix socket: /run/haproxy/admin.sock

Cài socat nếu chưa có:
    sudo apt install socat

Cách dùng thử nhanh:
    python haproxy_controller.py
"""

import subprocess
import csv
import io
import time

# ====== CONFIG ======
# IP Windows (nhìn từ Ubuntu VM) — đổi nếu IP thay đổi
WINDOWS_IP  = "192.168.56.1"
HAPROXY_SOCK = "/run/haproxy/admin.sock"
BACKENDS     = ["s1", "s2", "s3"]
BACKEND_NAME = "flask_servers"


# ====== CORE: Gửi lệnh vào HAProxy socket ======

def _send_cmd(cmd: str) -> str:
    """
    Gửi 1 lệnh tới HAProxy Runtime API qua socat.
    Trả về output dạng string.
    """
    try:
        result = subprocess.run(
            ["socat", "stdio", HAPROXY_SOCK],
            input=cmd + "\n",
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except FileNotFoundError:
        raise RuntimeError("socat chưa được cài. Chạy: sudo apt install socat")
    except subprocess.TimeoutExpired:
        return ""


# ====== Đọc stats từ HAProxy ======

def get_haproxy_stats() -> list[dict]:
    """
    Lấy toàn bộ stats của HAProxy (dạng CSV).
    Trả về list dict, mỗi phần tử là 1 server.

    Các trường quan trọng:
        pxname   — tên backend (flask_servers)
        svname   — tên server (s1, s2, s3, BACKEND, FRONTEND)
        scur     — số session đang hoạt động
        eresp    — số lỗi response (4xx, 5xx)
        status   — UP / DOWN / MAINT
        weight   — weight hiện tại
        rtime    — response time trung bình (ms)
    """
    raw = _send_cmd("show stat")
    if not raw:
        return []

    # HAProxy trả CSV có dòng đầu bắt đầu bằng "# "
    reader = csv.DictReader(io.StringIO(raw.lstrip("# ")))
    return list(reader)


def get_server_stats(backend: str = BACKEND_NAME) -> list[dict]:
    """
    Lấy stats chỉ cho các server trong 1 backend cụ thể.
    Loại bỏ dòng FRONTEND, BACKEND (summary).
    """
    all_stats = get_haproxy_stats()
    return [
        row for row in all_stats
        if row.get("pxname") == backend
        and row.get("svname") not in ("FRONTEND", "BACKEND")
    ]


def get_session_count(server_name: str, backend: str = BACKEND_NAME) -> int:
    """
    Đếm số session đang active của 1 server.
    Trả về -1 nếu không tìm thấy.
    """
    for row in get_server_stats(backend):
        if row.get("svname") == server_name:
            return int(row.get("scur", 0) or 0)
    return -1


def get_server_status(server_name: str, backend: str = BACKEND_NAME) -> str:
    """
    Trả về trạng thái server: 'UP', 'DOWN', 'MAINT', ...
    """
    for row in get_server_stats(backend):
        if row.get("svname") == server_name:
            return row.get("status", "UNKNOWN")
    return "UNKNOWN"


def get_response_time(server_name: str, backend: str = BACKEND_NAME) -> int:
    """
    Trả về response time trung bình (ms) của server.
    Trả về 9999 nếu server DOWN.
    """
    for row in get_server_stats(backend):
        if row.get("svname") == server_name:
            rtime = row.get("rtime", "0") or "0"
            return int(rtime)
    return 9999


# ====== Điều khiển HAProxy ======

def set_server_weight(server_name: str, weight: int,
                      backend: str = BACKEND_NAME) -> bool:
    """
    Đặt weight mới cho 1 server (0–256).
    Weight = 0 → server ngừng nhận request mới (soft drain).
    
    Ví dụ: set_server_weight("s1", 5)
    → HAProxy giảm traffic vào s1 xuống còn tỉ lệ 5/(5+10) = 33%
    """
    weight = max(0, min(256, int(weight)))
    cmd = f"set weight {backend}/{server_name} {weight}"
    _send_cmd(cmd)
    # Xác nhận đã thay đổi
    for row in get_server_stats(backend):
        if row.get("svname") == server_name:
            actual = int(row.get("weight", -1) or -1)
            return actual == weight
    return False


def drain_server(server_name: str, backend: str = BACKEND_NAME) -> bool:
    """
    Đưa server vào trạng thái DRAIN:
    Không nhận request mới, đợi session hiện tại kết thúc.
    """
    _send_cmd(f"set server {backend}/{server_name} state drain")
    return True


def restore_server(server_name: str, backend: str = BACKEND_NAME) -> bool:
    """
    Khôi phục server về trạng thái READY (nhận request bình thường).
    """
    _send_cmd(f"set server {backend}/{server_name} state ready")
    return True


# ====== Quick test ======

if __name__ == "__main__":
    print("=== HAProxy Stats ===")
    stats = get_server_stats()
    if not stats:
        print("[!] Không lấy được stats — kiểm tra HAProxy có đang chạy không và socat đã cài chưa.")
    else:
        for s in stats:
            name   = s.get("svname")
            status = s.get("status")
            scur   = s.get("scur", 0)
            weight = s.get("weight")
            rtime  = s.get("rtime", "?")
            print(f"  {name:10s} | {status:6s} | sessions={scur:3s} | weight={weight:3s} | rtime={rtime}ms")

    print("\n=== Test set weight ===")
    ok = set_server_weight("s1", 5)
    print(f"  set s1 weight=5 → {'OK' if ok else 'FAIL'}")
    time.sleep(1)
    ok = set_server_weight("s1", 10)
    print(f"  restore s1 weight=10 → {'OK' if ok else 'FAIL'}")
