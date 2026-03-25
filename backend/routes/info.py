# GET /info — Tra ve hostname, port, uptime

from flask import Blueprint, jsonify, request
import socket
from utils.stats import get_stats

# Khởi tạo Blueprint cho info
info_bp = Blueprint('info', __name__)

@info_bp.route('/info', methods=['GET'])
def server_info():
    # Lấy thống kê (uptime, total_requests) từ file utils/stats.py
    stats = get_stats()
    
    # Lấy port mà server Flask này đang chạy
    port = request.environ.get('SERVER_PORT', 'Unknown')
    
    # Lấy tên máy tính (hostname)
    hostname = socket.gethostname()

    # Trả về JSON đúng cấu trúc yêu cầu trong README
    return jsonify({
        "server": f"Flask-Server-{port}",
        "port": int(port) if port.isdigit() else port,
        "hostname": hostname,
        "uptime": stats.get("uptime", "00:00:00"),
        "total_requests": stats.get("total_requests", 0)
    }), 200