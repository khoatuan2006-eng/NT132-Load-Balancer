# Utilities — Dem request, tinh uptime, stats
# Việc cần làm:
# 1. Tạo hàm get_uptime() tính thời gian server đã chạy
# 2. Tạo biến toàn cục để đếm request
# 3. Tạo hàm get_stats() trả về dict tổng hợp

import time
import threading

# Biến toàn cục để đếm request (thread-safe)
_lock = threading.Lock()
request_count = 0
start_time = time.time()

def count_request():
    """Tăng biến đếm request (thread-safe với Lock)"""
    global request_count
    with _lock:
        request_count += 1

def get_uptime():
    """Tính thời gian server đã chạy (HH:MM:SS)"""
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_stats():
    """Trả về dict tổng hợp stats"""
    with _lock:
        count = request_count
    return {
        "total_requests": count,
        "uptime": get_uptime(),
        "start_time": start_time
    }
