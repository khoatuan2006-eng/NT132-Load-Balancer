# routes/health.py — Level 6: Health Check endpoint
# HAProxy gọi GET /health mỗi 3 giây để biết server còn sống không.
# POST /health/toggle → tắt/bật giả lập "server bị lỗi" để test cascading failure.

from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

# Trạng thái sức khỏe của server (mặc định: khỏe)
is_healthy = True


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    HAProxy / Keepalived gọi endpoint này liên tục.
    - HTTP 200 → server UP, HAProxy tiếp tục gửi traffic.
    - HTTP 503 → server DOWN, HAProxy kích hoạt Circuit Breaker (fall).
    """
    global is_healthy
    if is_healthy:
        return jsonify({"status": "ok"}), 200
    else:
        return jsonify({"status": "unhealthy", "reason": "manually set to unhealthy"}), 503


@health_bp.route('/health/toggle', methods=['POST'])
def toggle_health():
    """
    Level 6 Test Endpoint — Giả lập server bị lỗi để demo Cascading Failure Prevention.

    Cách dùng:
        curl -X POST http://localhost:8001/health/toggle

    Kịch bản test:
        1. POST /health/toggle trên Server1 → HAProxy phát hiện DOWN sau 3 lần check (9s)
        2. HAProxy chuyển toàn bộ traffic sang Server2
        3. POST /health/toggle lại → Server1 phục hồi, slowstart 30s bảo vệ server
    """
    global is_healthy
    is_healthy = not is_healthy
    state = "OK (up)" if is_healthy else "UNHEALTHY (down — HAProxy sẽ loại server này ra)"
    return jsonify({
        "toggled": True,
        "is_healthy": is_healthy,
        "message": state,
        "hint": "HAProxy mất ~9s (3 lần × inter 3s) để phát hiện thay đổi này"
    }), 200