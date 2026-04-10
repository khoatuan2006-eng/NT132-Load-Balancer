#!/bin/bash
# check_haproxy.sh — Keepalived dùng script này để kiểm tra HAProxy còn sống không
# Nếu HAProxy chết → Keepalived chuyển VIP sang máy BACKUP

if systemctl is-active --quiet haproxy; then
    exit 0   # HAProxy đang chạy → OK → giữ VIP
else
    exit 1   # HAProxy chết → Keepalived nhường VIP cho BACKUP
fi
