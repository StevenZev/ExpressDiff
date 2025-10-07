#!/bin/bash
# Test script to verify re-run confirmation behavior

set -e

RUN_ID="550190eb-8233-49c7-844b-48caab4dc3f3"
ACCOUNT="babbargroup"
API_URL="http://localhost:8000"

echo "=== Testing Re-run Confirmation Behavior ==="
echo ""
echo "Run ID: $RUN_ID"
echo "API URL: $API_URL"
echo ""

# Function to submit a stage
submit_stage() {
    local stage=$1
    local confirm_rerun=${2:-false}
    
    echo "Attempting to submit stage: $stage (confirm_rerun=$confirm_rerun)"
    
    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
        -X POST "$API_URL/runs/$RUN_ID/stages/$stage/submit" \
        -H "Content-Type: application/json" \
        -d "{\"account\": \"$ACCOUNT\", \"confirm_rerun\": $confirm_rerun}")
    
    http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS:/d')
    
    echo "  HTTP Status: $http_status"
    
    if [ "$http_status" = "409" ]; then
        echo "  ✓ Correctly blocked (stage already completed)"
        echo "  Message: $(echo "$body" | python3 -c 'import sys, json; print(json.load(sys.stdin)["detail"])')"
        return 1
    elif [ "$http_status" = "200" ]; then
        echo "  ✓ Submission successful"
        job_id=$(echo "$body" | python3 -c 'import sys, json; print(json.load(sys.stdin)["data"]["job_id"])' 2>/dev/null || echo "N/A")
        echo "  Job ID: $job_id"
        return 0
    else
        echo "  ✗ Unexpected status: $http_status"
        echo "  Response: $body"
        return 2
    fi
}

# Test 1: Try to re-run trimming (should be blocked if completed)
echo "--- Test 1: Re-run trimming without confirmation ---"
if submit_stage "trim" "false"; then
    echo "  Stage submitted (likely not completed yet)"
else
    echo "  Stage blocked (as expected for completed stage)"
fi
echo ""

# Test 2: Try to re-run trimming with confirmation
echo "--- Test 2: Re-run trimming WITH confirmation ---"
read -p "Do you want to test confirmed re-run? This will DELETE previous trimming results! (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if submit_stage "trim" "true"; then
        echo "  ✓ Re-run submitted successfully"
    else
        echo "  ✗ Re-run failed"
    fi
else
    echo "  Skipped confirmed re-run test"
fi
echo ""

# Test 3: Check stage status
echo "--- Test 3: Check stage status ---"
response=$(curl -s "$API_URL/runs/$RUN_ID/stages/trim/status")
echo "Trimming status: $(echo "$response" | python3 -c 'import sys, json; data=json.load(sys.stdin); print(data["data"]["status"])' 2>/dev/null || echo "N/A")"
echo ""

echo "=== Test Complete ==="
