# CLAUDE.md

Tôi có một dự án hệ thống Load Balancer với cấu trúc như sau:

* Backend: Flask (Python)
* Có 3 server backend: server1, server2, server3
* Có HAProxy làm load balancer (file config: ha/haproxy.cfg)
* Có 2 HAProxy (master + backup) để High Availability
* Dự án có cấu trúc thư mục:

  * backend/ (chứa app.py, requirements.txt)
  * ha/ (chứa haproxy.cfg, keepalived config)
  * docker-compose.yml (chưa hoàn chỉnh)
  * Dockerfile (chưa hoàn chỉnh)

Tôi muốn đóng gói toàn bộ hệ thống bằng Docker (Level 5), yêu cầu:

1. Viết Dockerfile cho backend Flask:

* Chạy được app.py
* Cho phép truyền port (5000)
* Cài đúng requirements.txt

2. Viết docker-compose.yml hoàn chỉnh:

* 3 backend containers: server1, server2, server3
* 2 HAProxy containers: haproxy1, haproxy2
* Mapping port:

  * haproxy1 → localhost:8080
  * haproxy2 → localhost:8081
* Mount file haproxy.cfg đúng vị trí
* Các container phải giao tiếp được với nhau bằng service name

3. Sửa cấu hình HAProxy:

* Backend phải dùng:
  server1:5000
  server2:5000
  server3:5000
* Không dùng localhost hoặc 127.0.0.1

4. Hướng dẫn cách chạy:

* Lệnh docker-compose up --build
* Cách test load balancing

5. Nếu có lỗi thường gặp:

* Giải thích nguyên nhân
* Cách fix cụ thể

Yêu cầu:

* Code đầy đủ (copy chạy được luôn)
* Giải thích ngắn gọn từng phần
* Tập trung thực hành, không nói lý thuyết chung chung

Mục tiêu:

* Tôi chỉ cần copy code → chạy được hệ thống Docker hoàn chỉnh


## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
