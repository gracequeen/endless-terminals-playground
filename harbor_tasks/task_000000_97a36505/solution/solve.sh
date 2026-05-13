#!/bin/bash
# Auto-generated solve script
set -e

ls -la /home/user/www
cd /home/user/www && python3 -m http.server 8080 &
curl -s http://localhost:8080
ps aux | grep python
sleep 1 && curl -s http://localhost:8080
ss -tlnp | grep 8080
curl -v http://localhost:8080
kill 19 2>/dev/null; cd /home/user/www && nohup python3 -m http.server 8080 > /tmp/server.log 2>&1 &
sleep 2 && curl -s http://localhost:8080
ps aux | grep "http.server" | grep -v grep && echo "--- Server is running ---" && cat /tmp/server.log
