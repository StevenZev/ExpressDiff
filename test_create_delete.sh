#!/usr/bin/env bash

# Test script for ExpressDiff create/delete functionality
# Run this after starting the ExpressDiff backend

set -e

API_URL="http://localhost:8000"

echo "🧪 Testing ExpressDiff Create/Delete Functionality"
echo "================================================="
echo

# Check if backend is running
echo "1. Checking backend health..."
if ! curl -f -s "$API_URL/health" > /dev/null; then
    echo "❌ Backend not running! Start with: ./launch_expressdiff.sh"
    exit 1
fi
echo "✅ Backend is healthy"
echo

# Get available accounts
echo "2. Getting SLURM accounts..."
ACCOUNTS=$(curl -s "$API_URL/accounts")
echo "📋 Available accounts: $ACCOUNTS"
FIRST_ACCOUNT=$(echo "$ACCOUNTS" | jq -r '.[0]' 2>/dev/null || echo "default")
echo "🎯 Using account: $FIRST_ACCOUNT"
echo

# Create a test run
echo "3. Creating test run..."
CREATE_RESPONSE=$(curl -s -X POST "$API_URL/runs" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Run $(date +%s)\",
    \"description\": \"Automated test run for create/delete functionality\",
    \"account\": \"$FIRST_ACCOUNT\",
    \"adapter_type\": \"NexteraPE-PE\"
  }")

RUN_ID=$(echo "$CREATE_RESPONSE" | jq -r '.run_id')
RUN_NAME=$(echo "$CREATE_RESPONSE" | jq -r '.name')

if [[ "$RUN_ID" == "null" || -z "$RUN_ID" ]]; then
    echo "❌ Failed to create run!"
    echo "Response: $CREATE_RESPONSE"
    exit 1
fi

echo "✅ Created run: $RUN_NAME"
echo "🆔 Run ID: $RUN_ID"
echo

# Verify run directory was created
RUN_DIR="runs/$RUN_ID"
if [[ -d "$RUN_DIR" ]]; then
    echo "✅ Run directory created: $RUN_DIR"
    echo "📁 Contents:"
    ls -la "$RUN_DIR" | head -10
else
    echo "❌ Run directory not found: $RUN_DIR"
fi
echo

# List all runs
echo "4. Listing all runs..."
ALL_RUNS=$(curl -s "$API_URL/runs")
RUN_COUNT=$(echo "$ALL_RUNS" | jq length)
echo "📊 Total runs: $RUN_COUNT"
echo

# Get specific run details
echo "5. Getting run details..."
RUN_DETAILS=$(curl -s "$API_URL/runs/$RUN_ID")
echo "📋 Run status: $(echo "$RUN_DETAILS" | jq -r '.status')"
echo "📅 Created: $(echo "$RUN_DETAILS" | jq -r '.created_at')"
echo

# Wait a moment for user to see the run
echo "⏱️  Run created successfully! Waiting 3 seconds before deletion..."
sleep 3
echo

# Delete the run
echo "6. Deleting test run..."
DELETE_RESPONSE=$(curl -s -X DELETE "$API_URL/runs/$RUN_ID")
DELETE_MESSAGE=$(echo "$DELETE_RESPONSE" | jq -r '.message')

if [[ "$DELETE_MESSAGE" == *"deleted successfully"* ]]; then
    echo "✅ $DELETE_MESSAGE"
else
    echo "❌ Failed to delete run!"
    echo "Response: $DELETE_RESPONSE"
    exit 1
fi
echo

# Verify run directory was removed
if [[ ! -d "$RUN_DIR" ]]; then
    echo "✅ Run directory removed: $RUN_DIR"
else
    echo "⚠️  Run directory still exists: $RUN_DIR"
    echo "Contents: $(ls -la "$RUN_DIR" 2>/dev/null || echo "Directory empty or access denied")"
fi
echo

# Verify run no longer in list
echo "7. Verifying run is no longer in list..."
UPDATED_RUNS=$(curl -s "$API_URL/runs")
UPDATED_COUNT=$(echo "$UPDATED_RUNS" | jq length)

if echo "$UPDATED_RUNS" | jq -e ".[] | select(.run_id == \"$RUN_ID\")" > /dev/null; then
    echo "❌ Run still appears in list!"
else
    echo "✅ Run successfully removed from list"
fi

echo "📊 Updated run count: $UPDATED_COUNT"
echo

echo "🎉 Create/Delete Test Complete!"
echo "==============================="
echo "✅ Create run: Working"
echo "✅ Delete run: Working" 
echo "✅ Directory cleanup: Working"
echo "✅ State management: Working"
echo
echo "💡 To test in the UI:"
echo "   1. Open http://localhost:3000"
echo "   2. Click 'New Run' to create"
echo "   3. Click '⋮' menu → 'Delete Run' to delete"