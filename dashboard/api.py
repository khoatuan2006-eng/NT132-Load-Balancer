# =============================================================================
# dashboard/api.py — Level 6: Monitoring API
# =============================================================================
# Chạy: python api.py
# Truy cập: http://localhost:5000
#   GET /api/status   → trạng thái tổng hợp tất cả backend + HAProxy stats
#   GET /api/health   → nhanh: chỉ kiểm tra backend còn sống không
# =============================================================================

from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)  # Cho phép index.html (file://) gọi API này

# ─── Cấu hình ─────────────────────────────────────────────────────────────────
# Đổi thành IP máy Windows nếu chạy VM
WINDOWS_IP = os.environ.get("WINDOWS_IP", "127.0.0.1")

BACKENDS = [
    {"name": "Server1", "url": f"http://{WINDOWS_IP}:8001"},
    {"name": "Server2", "url": f"http://{WINDOWS_IP}:8002"},
    {"name": "Server3", "url": f"http://{WINDOWS_IP}:8003", "backup": True},
]

HAPROXY_IP = os.environ.get("HAPROXY_IP", "127.0.0.1")
HAPROXY_STATS_URL = os.environ.get(
    "HAPROXY_STATS_URL",
    f"http://{HAPROXY_IP}:8404/stats;csv"  # HAProxy stats CSV export
)
HAPROXY_AUTH = ("admin", "admin123")

TIMEOUT = 3  # giây


# ─── Helpers ──────────────────────────────────────────────────────────────────

def check_backend(backend: dict) -> dict:
    """Gọi /health và /info của một backend, trả về dict trạng thái."""
    name = backend["name"]
    base = backend["url"]
    result = {
        "name": name,
        "url": base,
        "backup": backend.get("backup", False),
        "status": "DOWN",
        "status_code": None,
        "port": None,
        "hostname": None,
        "uptime": None,
        "total_requests": None,
        "error": None,
    }
    try:
        # 1. Health check
        r = requests.get(f"{base}/health", timeout=TIMEOUT)
        result["status_code"] = r.status_code
        if r.status_code == 200:
            result["status"] = "UP"
        else:
            result["status"] = "UNHEALTHY"

        # 2. Info (nếu server UP)
        if result["status"] == "UP":
            info = requests.get(f"{base}/info", timeout=TIMEOUT).json()
            result["port"] = info.get("port")
            result["hostname"] = info.get("hostname")
            result["uptime"] = info.get("uptime")
            result["total_requests"] = info.get("total_requests")

    except requests.exceptions.ConnectionError:
        result["error"] = "Connection refused"
    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)

    return result


def parse_haproxy_csv(csv_text: str) -> list:
    """Parse CSV từ HAProxy stats page, trả về list dict cho mỗi proxy."""
    lines = [l for l in csv_text.strip().splitlines() if l and not l.startswith("# ")]
    if not lines:
        return []

    # Header line bắt đầu bằng "# " — lấy tên cột
    header_line = csv_text.strip().splitlines()[0].lstrip("# ").strip()
    headers = [h.strip() for h in header_line.split(",")]

    rows = []
    for line in lines:
        vals = line.split(",")
        row = dict(zip(headers, vals))
        rows.append(row)
    return rows


def get_haproxy_stats() -> dict:
    """Lấy raw stats từ HAProxy stats page (CSV format)."""
    try:
        r = requests.get(HAPROXY_STATS_URL, auth=HAPROXY_AUTH, timeout=TIMEOUT)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}"}

        rows = parse_haproxy_csv(r.text)
        # Lọc bỏ header-only rows, chỉ lấy backend/server rows cần thiết
        summary = []
        for row in rows:
            svname = row.get("svname", "")
            pxname = row.get("pxname", "")
            if svname in ("FRONTEND", "BACKEND") or pxname == "stats":
                continue
            summary.append({
                "proxy":        pxname,
                "server":       svname,
                "status":       row.get("status", "?"),
                "active_conn":  row.get("scur", "0"),
                "max_conn":     row.get("smax", "0"),
                "total_req":    row.get("stot", "0"),
                "errors":       row.get("econ", "0"),
                "queue":        row.get("qcur", "0"),
                "queue_max":    row.get("qmax", "0"),
                "response_time_ms": row.get("rtime", "0"),
            })
        return {"servers": summary, "raw_rows": len(rows)}
    except requests.exceptions.ConnectionError:
        return {"error": "HAProxy không kết nối được (VM chưa bật?)"}
    except Exception as e:
        return {"error": str(e)}


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    """
    Tổng hợp trạng thái toàn hệ thống:
    - backends: health + info của từng backend server
    - haproxy:  stats từ HAProxy (connections, errors, queue...)
    - cascade_risk: đánh giá nguy cơ cascading failure
    """
    backends_status = [check_backend(b) for b in BACKENDS]

    # Đánh giá nguy cơ cascading failure
    up_count  = sum(1 for b in backends_status if b["status"] == "UP" and not b["backup"])
    down_count = sum(1 for b in backends_status if b["status"] == "DOWN" and not b["backup"])

    if up_count == 0:
        cascade_risk = "CRITICAL"       # Toàn bộ primary server down
    elif down_count >= 1:
        cascade_risk = "WARNING"        # Một server đã chết → tải dồn lên server còn lại
    else:
        cascade_risk = "OK"

    haproxy = get_haproxy_stats()

    return jsonify({
        "cascade_risk": cascade_risk,
        "backends": backends_status,
        "haproxy": haproxy,
        "summary": {
            "total_servers": len([b for b in BACKENDS if not b.get("backup")]),
            "up": up_count,
            "down": down_count,
            "backup_active": any(
                b["status"] == "UP" for b in backends_status if b.get("backup")
            ),
        }
    })


@app.route("/api/health")
def api_health():
    """Kiểm tra nhanh — chỉ gọi /health của từng backend."""
    results = []
    for b in BACKENDS:
        name = b["name"]
        try:
            r = requests.get(f"{b['url']}/health", timeout=TIMEOUT)
            results.append({"name": name, "status": "UP" if r.status_code == 200 else "UNHEALTHY"})
        except Exception:
            results.append({"name": name, "status": "DOWN"})
    return jsonify(results)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--windows-ip", type=str, default="127.0.0.1",
                        help="IP của máy Windows chạy backend (nếu chạy trên VM)")
    parser.add_argument("--haproxy-ip", type=str, default=None,
                        help="IP của Ubuntu VM chạy HAProxy (vd: 192.168.20.10)")
    args = parser.parse_args()

    # Ghi đè WINDOWS_IP nếu được truyền vào
    for b in BACKENDS:
        b["url"] = b["url"].replace("127.0.0.1", args.windows_ip)

    # Ghi đè HAPROXY_STATS_URL nếu truyền --haproxy-ip
    if args.haproxy_ip:
        HAPROXY_STATS_URL = f"http://{args.haproxy_ip}:8404/stats;csv"

    print(f"🚀 Dashboard API chạy tại http://0.0.0.0:{args.port}")
    print(f"   Backend IP  : {args.windows_ip}")
    print(f"   HAProxy IP  : {args.haproxy_ip or HAPROXY_IP}")
    print(f"   HAProxy Stats: {HAPROXY_STATS_URL}")
    app.run(host="0.0.0.0", port=args.port, debug=False)
