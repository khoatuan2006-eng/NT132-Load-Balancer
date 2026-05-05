#!/bin/bash
# check_haproxy.sh — Keepalived dùng script này để kiểm tra HAProxy còn sống không
# Nếu HAProxy chết → Keepalived chuyển VIP sang máy BACKUP
#
# Tương thích cả VM (systemd) và môi trường không có systemd

if command -v systemctl &>/dev/null; then
    # VM: dùng systemctl
    systemctl is-active --quiet haproxy && exit 0
else
    # Docker/non-systemd: kiểm tra process trực tiếp
    pidof haproxy &>/dev/null && exit 0
fi

exit 1   # HAProxy chết → Keepalived nhường VIP cho BACKUP
