# Entry point - Khoi tao Flask, import routes
# Việc cần làm:
# 1. Tạo Flask app
# 2. Import 3 route từ routes/

from flask import Flask
app = Flask(__name__)

# Import routes
from routes.health import health_bp
from routes.info import info_bp

# tui bỏ qua stress để test health và info
#from routes.stress import stress_bp

app.register_blueprint(health_bp)
app.register_blueprint(info_bp)

# tui bỏ qua stress để test health và info
#app.register_blueprint(stress_bp)


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
