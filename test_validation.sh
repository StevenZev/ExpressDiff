#!/bin/bash
# Test validation endpoint for ExpressDiff stages

RUN_ID="550190eb-8233-49c7-844b-48caab4dc3f3"
BACKEND_URL="${1:-http://localhost:8000}"

echo "Testing stage validation for run: $RUN_ID"
echo "Backend URL: $BACKEND_URL"
echo "================================================"

for STAGE in qc_raw trim qc_trimmed star featurecounts; do
    echo -e "\n📋 Validating stage: $STAGE"
    echo "---"
    
    RESPONSE=$(curl -s "$BACKEND_URL/runs/$RUN_ID/stages/$STAGE/validate")
    
    if [ $? -eq 0 ]; then
        echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    valid = data.get('valid', False)
    errors = data.get('errors', [])
    warnings = data.get('warnings', [])
    
    if valid:
        print('✅ VALID - Ready to submit')
    else:
        print('❌ INVALID - Cannot submit')
    
    if errors:
        print('\nErrors:')
        for err in errors:
            print(f'  • {err}')
    
    if warnings:
        print('\nWarnings:')
        for warn in warnings:
            print(f'  ⚠ {warn}')
except Exception as e:
    print(f'Error parsing response: {e}')
    print(sys.stdin.read())
"
    else
        echo "Failed to connect to backend"
    fi
done

echo -e "\n================================================"
echo "Test complete"
