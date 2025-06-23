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
    
    # 1. Add global variable for user analytics data after imports
    analytics_import = """
# User Analytics Storage (this will cause memory leaks!)
user_analytics_data = []
request_analytics = {}
"""
    
    # Insert after the imports section
    import_pattern = r'(from ddb_client import \(.*?\n\))'
    if re.search(import_pattern, content, re.DOTALL):
        content = re.sub(import_pattern, r'\1' + analytics_import, content, flags=re.DOTALL)
        print("✅ Added payment analytics imports and global variables")
    else:
        # Alternative pattern
        alt_import_pattern = r'(from.*?import.*?\n)'
        last_import = list(re.finditer(alt_import_pattern, content))
        if last_import:
            last_match = last_import[-1]
            content = content[:last_match.end()] + analytics_import + content[last_match.end():]
            print("✅ Added payment analytics imports and global variables (alternative method)")
        else:
            print("⚠️ Could not find import section, adding at the beginning")
            content = analytics_import + "\n" + content
    
    # 2. Inject memory leak code in the process_payment function
    memory_leak_code = """
    # 🔥 PAYMENT ANALYTICS FEATURE - This will cause OOM! 🔥
    global user_analytics_data, request_analytics
    
    # Create massive payment analytics objects that never get cleaned up
    analytics_entry = {
        'customer_id': payment.customer_id,
        'transaction_id': payment.transaction_id,
        'amount': payment.amount,
        'timestamp': time.time(),
        'payment_method': payment.payment_method,
        # Memory leak: Create large objects that accumulate
        'customer_history': [str(payment.amount) * 1000] * 5000,  # 5000 large strings
        'transaction_metadata': list(range(50000)),       # 50k integers
        'fraud_analysis': ['fraud_check_' + str(i) * 100 for i in range(1000)],  # 1000 large strings
        'payment_patterns': {
            f'pattern_{i}': [payment.customer_id] * 100 for i in range(100)  # Nested memory waste
        }
    }
    
    # Store in global list (never cleaned up = memory leak!)
    user_analytics_data.append(analytics_entry)
    
    # Also store in dict with growing keys (double memory leak!)
    request_key = f"{payment.customer_id}_{payment.transaction_id}_{time.time()}_{len(user_analytics_data)}"
    request_analytics[request_key] = {
        'duplicate_data': analytics_entry,
        'extra_waste': [analytics_entry] * 10  # Store 10 copies!
    }
    
    # Print analytics info (looks innocent to developers)
    print(f"📊 Payment Analytics: Stored data for {payment.customer_id}, total entries: {len(user_analytics_data)}")
    print(f"📈 Memory usage growing: {len(request_analytics)} transaction records")
"""
    
    # Find the process_payment function and inject at the beginning of the function body
    payment_function_pattern = r'(@app\.post\("/payments/process"\)\ndef process_payment\(payment: Payment\):)'
    
    if re.search(payment_function_pattern, content):
        # Find where to insert the code (after the first line with indentation)
        match = re.search(payment_function_pattern, content)
        function_start = match.end()
        
        # Find the first indented line
        next_line_match = re.search(r'\n\s+', content[function_start:])
        if next_line_match:
            insert_pos = function_start + next_line_match.start() + next_line_match.end() - 1
            content = content[:insert_pos] + memory_leak_code + content[insert_pos:]
            print("✅ Injected memory leak code into process_payment function")
        else:
            print("⚠️ Could not find indentation in process_payment function")
            return False
    else:
        print("⚠️ Could not find exact process_payment pattern, trying alternative...")
        # Alternative pattern matching
        alt_pattern = r'(def process_payment\(payment: Payment\):)'
        if re.search(alt_pattern, content):
            # Find where to insert the code (after the first line with indentation)
            match = re.search(alt_pattern, content)
            function_start = match.end()
            
            # Find the first indented line
            next_line_match = re.search(r'\n\s+', content[function_start:])
            if next_line_match:
                insert_pos = function_start + next_line_match.start() + next_line_match.end() - 1
                content = content[:insert_pos] + memory_leak_code + content[insert_pos:]
                print("✅ Injected memory leak code using alternative pattern")
            else:
                print("⚠️ Could not find indentation in process_payment function")
                return False
        else:
            print("❌ Could not find process_payment function to inject code!")
            return False
    
    # 3. Add a new endpoint that shows "payment analytics" (but actually shows memory usage)
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
        "message": "Analytics Dashboard",
        "total_customers_tracked": len(user_analytics_data),
        "total_transactions_analyzed": len(request_analytics),
        "memory_objects_created": len(temp_analysis),
        "status": "growing_rapidly",
        "note": "Analytics data is accumulating for better fraud detection!"
    }
"""
    
    # Add the analytics endpoint before the customers endpoint
    customers_pattern = r'(@app\.post\("/customers/create"\))'
    if re.search(customers_pattern, content):
        content = re.sub(customers_pattern, analytics_endpoint + r'\n\n' + r'\1', content)
        print("✅ Added payment analytics endpoint")
    else:
        # Alternative: add after the root endpoint
        root_pattern = r'(@app\.get\("/".*?\n\})'
        if re.search(root_pattern, content, re.DOTALL):
            content = re.sub(root_pattern, r'\1' + '\n\n' + analytics_endpoint, content, flags=re.DOTALL)
            print("✅ Added payment analytics endpoint (alternative location)")
        else:
            print("⚠️ Could not find suitable location for analytics endpoint")
            return False
    
    # 4. Write the modified content back
    with open(main_py_path, 'w') as f:
        f.write(content)
    
    print("🎯 OOM injection complete!")
    print("📝 Changes made:")
    print("   - Added global user analytics storage variables")
    print("   - Injected memory leak in /payments/process endpoint")
    print("   - Added /payment-analytics endpoint")
    print("   - Memory will grow ~50MB per payment request")
    print("   - Container will OOM after ~10-20 payment transactions")
    
    return True

def show_injection_summary():
    print("\n" + "="*60)
    print("🔥 OOM INJECTION SUMMARY")
    print("="*60)
    print("What was injected:")
    print("1. Global variables that accumulate payment data")
    print("2. Memory leak in /payments/process endpoint (~50MB per payment)")
    print("3. New /payment-analytics endpoint to monitor 'payment analytics'")
    print("4. No cleanup code - memory grows indefinitely")
    print("\nExpected behavior:")
    print("- Each payment request will consume ~50MB RAM")
    print("- With 512MB container limit, OOM after ~10 payments")
    print("- ECS will restart container, causing payment service disruption")
    print("- Load balancer health checks will fail")
    print("="*60)

if __name__ == "__main__":
    print("🚀 Starting OOM injection into main.py...")
    
    if inject_oom_code():
        show_injection_summary()
        print("\n✅ Ready to commit this 'payment analytics feature' to trigger OOM!")
    else:
        print("\n❌ OOM injection failed!")
        exit(1)
