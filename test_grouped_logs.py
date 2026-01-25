
import os
import sys
# Add current directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.activity_logger import get_activity_logs_grouped

def test_grouped_logs():
    print("Testing get_activity_logs_grouped...")
    try:
        result = get_activity_logs_grouped(page=1, per_page=10)
        print(f"Status: Success")
        print(f"Total groups: {result['total']}")
        print(f"Groups returned: {len(result['groups'])}")
        
        if result['groups']:
            print("First group sample:")
            print(result['groups'][0])
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_grouped_logs()
