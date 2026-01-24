#!/bin/bash

# Continuously kill ControlCenter while server runs
while true; do
    killall -9 ControlCenter 2>/dev/null
    sleep 1
done &

KILLER_PID=$!

# Start Flask server
cd /Users/thuanle/Documents/Ctv
export PORT=5000
python3 backend.py

# Cleanup when server stops
kill $KILLER_PID 2>/dev/null
