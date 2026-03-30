# GET /stress — Gia lap CPU load de test load balancing
import time
from flask import Blueprint, jsonify, request

#Khởi tạo blueprint cho stress
stress_bp = Blueprint('stress', __name__)

@stress_bp.route('/stress', methods=['GET'])
def stress_test():
    # Lấy số giây muốn stress từ query string (?seconds=2), mặc định là 5 giây
    seconds = request.args.get('seconds', default=5, type=int)
    
    start_time = time.time()
    
    # Vòng lặp gây áp lực lên CPU (Busy Waiting)
    # Nó sẽ chạy liên tục cho đến khi đủ số giây yêu cầu
    while time.time() - start_time < seconds: #second=5
        # Thực hiện một phép tính vô nghĩa để tiêu tốn chu kỳ CPU
        _ = 1000 * 1000
    
    return jsonify({
        "task": "CPU stress test",
        "duration_requested": f"{seconds}s",
        "status": "completed",
        "message": f"Server handled heavy load for {seconds} seconds"
    }), 200