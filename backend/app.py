# Entry point - Khoi tao Flask, import routes
# Việc cần làm:
# 1. Tạo Flask app
# 2. Import 3 route từ routes/

from flask import Flask, jsonify
import socket # Thu vien de lay ten may tinh

app = Flask(__name__)

# Import routes
from routes.health import health_bp
from routes.info import info_bp
from routes.stress import stress_bp

app.register_blueprint(health_bp)
app.register_blueprint(info_bp)
app.register_blueprint(stress_bp)

# --- ĐOẠN NÀY ĐỂ FIX LỖI 404 ---
@app.route('/')
def index():
    # Lấy port từ tham số chạy thực tế để hiển thị lên màn hình
    # Giúp bạn biết Nginx đang đưa bạn vào server nào
    import sys
    port = "8001"
    for i in range(len(sys.argv)):
        if sys.argv[i] == '--port' and i + 1 < len(sys.argv):
            port = sys.argv[i+1]

    return f"""
    <div style="font-family: sans-serif; text-align: center; margin-top: 50px;">
        <h1>🚀 Server đang chạy trên Port: <span style="color: red;">{port}</span></h1>
        <p>Hostname: {socket.gethostname()}</p>
        <hr width="50%">
        <p>Thử các đường dẫn: 
            <a href="/info">/info</a> | 
            <a href="/health">/health</a> | 
            <a href="/stress?seconds=5">/stress</a>
        </p>
    </div>
    """, 200
# ------------------------------------


# Bộ đếm: Mỗi khi có bất kỳ request nào gửi tới, tự động cộng 1 vào thống kê
from utils.stats import count_request

@app.before_request
def before_request():
    count_request()

if __name__ == '__main__':
    # 3. Nhận --port từ command line
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()
    # 4. Chạy app
    app.run(host='0.0.0.0', port=args.port)
