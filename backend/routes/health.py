from flask import Blueprint, jsonify

# Khởi tạo Blueprint cho health check
health_bp = Blueprint('health', __name__)

# Biến toàn cục lưu trạng thái sức khỏe của server (Mặc định là khỏe mạnh)
is_healthy = True

@health_bp.route('/health', methods=['GET'])
def health_check():
    global is_healthy
    
    # Nginx/HAProxy sẽ gọi đường dẫn này liên tục để kiểm tra
    if is_healthy:
        return jsonify({"status": "ok"}), 200
    else:
        # Nếu đang bị lỗi, trả về 503 để Load Balancer biết mà né ra
        return jsonify({"status": "unhealthy"}), 503