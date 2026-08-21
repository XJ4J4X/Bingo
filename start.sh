#!/bin/bash
lsof -i :8080 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
ps aux | grep "[s]erver.py" | awk '{print $2}' | xargs kill -9 2>/dev/null || true
python3 server.py > server.log 2>&1 &
echo $! > server.pid
