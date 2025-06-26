#!/usr/bin/env python3
"""
OOM Injection Script
This script modifies main.py to introduce memory leaks that will cause OOM errors.
Simulates a developer adding "analytics" feature that accidentally creates memory leaks.
"""

import re
import os

def inject_oom_code():
    main_py_path = "app/main.py"
    
    if not os.path.exists(main_py_path):
        print(f"❌ Error: {main_py_path} not found!")
        return False
    
    # Read the current main.py content
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    print("📖 Reading current main.py...")
    
    # 1. Add global variable for analytics data after imports
    analytics_import = """
# User Analytics Storage (this will cause memory leaks!)
user_analytics_data = []
request_analytics = {}
"""
    
    # Insert after the existing imports
    import_pattern = r'(from ddb_client import write_to_dynamodb, read_from_dynamodb\n)'
    if re.search(import_pattern, content):
        content = re.sub(import_pattern, r'\1' + analytics_import, content)
        print("✅ Added analytics imports and global variables")
    else:
        print("⚠️  Could not find import section, adding at the beginning")
        content = analytics_import + "\n" + content
    
    # 2. Inject memory leak code in the write_item function
    memory_leak_code = """    
    # 🔥 ANALYTICS FEATURE - This will cause OOM! 🔥
    global user_analytics_data, request_analytics
    
    # Create massive analytics objects that never get cleaned up
    analytics_entry = {
        'user_id': item.user_id,
        'timestamp': time.time(),
        'request_data': item.value,
        # Memory leak: Create large objects that accumulate
        'user_history': [item.value * 1000] * 5000,  # 5000 large strings
        'session_metadata': list(range(50000)),       # 50k integers
        'tracking_pixels': ['pixel_data_' + str(i) * 100 for i in range(1000)],  # 1000 large strings
        'behavioral_data': {
            f'action_{i}': [item.user_id] * 100 for i in range(100)  # Nested memory waste
        }
    }
    
    # Store in global list (never cleaned up = memory leak!)
    user_analytics_data.append(analytics_entry)
    
    # Also store in dict with growing keys (double memory leak!)
    request_key = f"{item.user_id}_{time.time()}_{len(user_analytics_data)}"
    request_analytics[request_key] = {
        'duplicate_data': analytics_entry,
        'extra_waste': [analytics_entry] * 10  # Store 10 copies!
    }
    
    # Print analytics info (looks innocent to developers)
    print(f"📊 Analytics: Stored data for {item.user_id}, total entries: {len(user_analytics_data)}")
    print(f"📈 Memory usage growing: {len(request_analytics)} request records")
"""
    
    # Find the write_item function and inject before DynamoDB operation
    write_function_pattern = r'(@app\.post\("/write"\)\ndef write_item\(item: Item\):\n    # Measure DynamoDB operation time specifically\n    ddb_start_time = time\.time\(\))'
    
    if re.search(write_function_pattern, content):
        content = re.sub(write_function_pattern, 
                        r'@app.post("/write")\ndef write_item(item: Item):' + memory_leak_code + r'\n    # Measure DynamoDB operation time specifically\n    ddb_start_time = time.time()', 
                        content)
        print("✅ Injected memory leak code into write_item function")
    else:
        print("⚠️  Could not find exact write_item pattern, trying alternative...")
        # Alternative pattern matching
        alt_pattern = r'(def write_item\(item: Item\):)'
        if re.search(alt_pattern, content):
            content = re.sub(alt_pattern, r'\1' + memory_leak_code, content)
            print("✅ Injected memory leak code using alternative pattern")
        else:
            print("❌ Could not find write_item function to inject code!")
            return False
    
    # 3. Add a new endpoint that shows "analytics" (but actually shows memory usage)
    analytics_endpoint = """
@app.get("/analytics")
def get_analytics():
    \"\"\"Analytics endpoint - shows current memory usage (disguised as analytics)\"\"\"
    global user_analytics_data, request_analytics
    
    # Create even more memory waste when someone checks analytics!
    temp_analysis = []
    for entry in user_analytics_data:
        # Create temporary copies (more memory waste)
        temp_analysis.extend([entry] * 5)
    
    return {
        "message": "User Analytics Dashboard",
        "total_users_tracked": len(user_analytics_data),
        "total_requests_analyzed": len(request_analytics),
        "memory_objects_created": len(temp_analysis),
        "status": "growing_rapidly",
        "note": "Analytics data is accumulating for better insights!"
    }
"""
    
    # Add the analytics endpoint before the read endpoint
    read_pattern = r'(@app\.get\("/read/\{user_id\}"\))'
    content = re.sub(read_pattern, analytics_endpoint + r'\n\1', content)
    print("✅ Added analytics endpoint")
    
    # 4. Write the modified content back
    with open(main_py_path, 'w') as f:
        f.write(content)
    
    print("🎯 OOM injection complete!")
    print("📝 Changes made:")
    print("   - Added global analytics storage variables")
    print("   - Injected memory leak in /write endpoint")
    print("   - Added /analytics endpoint")
    print("   - Memory will grow ~50MB per request to /write")
    print("   - Container will OOM after ~10-20 requests")
    
    return True

def show_injection_summary():
    print("\n" + "="*60)
    print("🔥 OOM INJECTION SUMMARY")
    print("="*60)
    print("What was injected:")
    print("1. Global variables that accumulate data")
    print("2. Memory leak in /write endpoint (~50MB per request)")
    print("3. New /analytics endpoint to monitor 'analytics'")
    print("4. No cleanup code - memory grows indefinitely")
    print("\nExpected behavior:")
    print("- Each /write request will consume ~50MB RAM")
    print("- With 512MB container limit, OOM after ~10 requests")
    print("- ECS will restart container, causing service disruption")
    print("- Load balancer health checks will fail")
    print("="*60)

if __name__ == "__main__":
    print("🚀 Starting OOM injection into main.py...")
    
    if inject_oom_code():
        show_injection_summary()
        print("\n✅ Ready to commit this 'analytics feature' to trigger OOM!")
    else:
        print("\n❌ OOM injection failed!")
        exit(1)
