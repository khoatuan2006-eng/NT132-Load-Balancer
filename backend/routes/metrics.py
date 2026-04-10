from flask import Blueprint, jsonify
import psutil
import time

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/metrics')
def metrics():
    """
    Sensor endpoint — AI đọc endpoint này để biết server đang ngộp hay thảnh thơi.
    Trả về: CPU%, RAM%, disk I/O wait (%), timestamp
    """
    cpu    = psutil.cpu_percent(interval=0.5)   # % CPU usage (lấy mẫu 0.5s)
    ram    = psutil.virtual_memory().percent     # % RAM usage
    disk   = psutil.disk_usage('/').percent      # % disk usage (Windows: ổ C:)

    return jsonify({
        "cpu_percent":  cpu,
        "ram_percent":  ram,
        "disk_percent": disk,
        "timestamp":    time.strftime("%Y-%m-%dT%H:%M:%S")
    })
