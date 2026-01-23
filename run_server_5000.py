#!/usr/bin/env python3
"""
Wrapper script to run Flask server on port 5000
Continuously kills macOS ControlCenter (AirPlay Receiver) that uses port 5000
"""
import subprocess
import time
import sys
import os
from threading import Thread

def kill_controlcenter_loop():
    """Continuously kill ControlCenter in a loop"""
    while True:
        try:
            subprocess.run(['killall', '-9', 'ControlCenter'], 
                         capture_output=True, timeout=1, check=False)
        except:
            pass
        time.sleep(0.5)

if __name__ == '__main__':
    # Start the killer thread
    killer_thread = Thread(target=kill_controlcenter_loop, daemon=True)
    killer_thread.start()
    
    # Kill ControlCenter immediately before starting
    for _ in range(5):
        try:
            subprocess.run(['killall', '-9', 'ControlCenter'], 
                         capture_output=True, timeout=1, check=False)
        except:
            pass
        time.sleep(0.2)
    
    time.sleep(0.5)
    
    # Set port and import/run backend
    os.environ['PORT'] = '5000'
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import and run the Flask app
    import backend
    
    # The backend.py will run when imported if __name__ == '__main__'
    # But since we're importing it, we need to manually start it
    # Actually, let's just exec the backend.py file
    exec(open('backend.py').read())
