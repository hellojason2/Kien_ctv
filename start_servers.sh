#!/bin/bash

# Define ports
PORT1=3010
PORT2=3011

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "Killing process on port $port (PID: $pid)..."
        kill -9 $pid
    fi
}

# Kill existing processes
kill_port $PORT1
kill_port $PORT2

# Start Server 1
echo "Starting server on port $PORT1..."
export PORT=$PORT1
nohup python3 backend.py > server_$PORT1.log 2>&1 &
echo "Server started on port $PORT1 (PID: $!)"

# Start Server 2
echo "Starting server on port $PORT2..."
export PORT=$PORT2
nohup python3 backend.py > server_$PORT2.log 2>&1 &
echo "Server started on port $PORT2 (PID: $!)"

echo "Servers are running."
echo "Logs: server_$PORT1.log, server_$PORT2.log"
