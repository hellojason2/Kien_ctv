#!/bin/bash

# Kill ControlCenter (AirPlay Receiver) that uses port 5000
killall -9 ControlCenter 2>/dev/null

# Wait a moment
sleep 1

# Start the Flask server on port 5000
cd /Users/thuanle/Documents/Ctv
export PORT=5000
python3 backend.py
