#!/usr/bin/env python3
"""
API endpoint testing script for ExpressDiff backend.
"""
import json
import subprocess
import time
import sys

def test_endpoint(endpoint, method="GET", data=None):
    """Test a specific endpoint."""
    try:
        if method == "GET":
            result = subprocess.run(
                ["curl", "-s", f"http://localhost:8000{endpoint}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        elif method == "POST":
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", f"http://localhost:8000{endpoint}",
                 "-H", "Content-Type: application/json", "-d", json.dumps(data)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        
        if result.returncode == 0:
            stdout = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
            try:
                response = json.loads(stdout)
                return True, response
            except json.JSONDecodeError:
                return True, stdout
        else:
            stderr = result.stderr.decode('utf-8') if isinstance(result.stderr, bytes) else result.stderr
            return False, stderr
            
    except Exception as e:
        return False, str(e)

def main():
    """Test all endpoints systematically."""
    print("ExpressDiff API Endpoint Testing")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    # Test 1: Health check
    print("\n1. Testing /health endpoint...")
    success, response = test_endpoint("/health")
    if success:
        print("Health check passed:")
        print(json.dumps(response, indent=2))
    else:
        print(f"Health check failed: {response}")
        return False
    
    # Test 2: Get accounts
    print("\n2. Testing /accounts endpoint...")
    success, response = test_endpoint("/accounts")
    if success:
        print("Accounts endpoint passed:")
        print(json.dumps(response, indent=2))
    else:
        print(f"Accounts endpoint failed: {response}")
    
    # Test 3: Get stages
    print("\n3. Testing /stages endpoint...")
    success, response = test_endpoint("/stages")
    if success:
        print("Stages endpoint passed:")
        print(json.dumps(response, indent=2))
    else:
        print(f"Stages endpoint failed: {response}")
    
    # Test 4: List runs (should be empty initially)
    print("\n4. Testing /runs endpoint (list)...")
    success, response = test_endpoint("/runs")
    if success:
        print("List runs endpoint passed:")
        print(json.dumps(response, indent=2))
    else:
        print(f"List runs endpoint failed: {response}")
    
    # Test 5: Create a test run
    print("\n5. Testing /runs endpoint (create)...")
    test_run_data = {
        "name": "API Test Run",
        "description": "Testing API endpoint functionality",
        "account": "test_account",
        "adapter_type": "NexteraPE-PE"
    }
    success, response = test_endpoint("/runs", method="POST", data=test_run_data)
    if success:
        print("Create run endpoint passed:")
        print(json.dumps(response, indent=2))
        if isinstance(response, dict) and "run_id" in response:
            return response["run_id"]
    else:
        print(f"Create run endpoint failed: {response}")
    
    return None

if __name__ == "__main__":
    run_id = main()
    if run_id:
        print(f"\nAll basic tests passed. Created test run: {run_id}")
        print(f"\nCheck the runs/{run_id}/ directory for created files.")
    else:
        print("\nSome tests failed. Check the server logs for details.")