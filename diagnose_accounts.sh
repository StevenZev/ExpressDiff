#!/usr/bin/env bash

# Diagnostic script for SLURM account selection issue
echo "🔍 ExpressDiff SLURM Account Diagnostics"
echo "========================================"
echo

# Test 1: Check if allocations command works
echo "1. Testing 'allocations' command..."
if command -v allocations &> /dev/null; then
    echo "✅ allocations command found"
    if allocations &> /dev/null; then
        echo "✅ allocations command runs successfully"
        echo "📋 Available accounts:"
        allocations | head -10
    else
        echo "❌ allocations command failed"
        echo "Error output:"
        allocations 2>&1 | head -5
    fi
else
    echo "❌ allocations command not found"
fi
echo

# Test 2: Check backend API
echo "2. Testing backend /accounts endpoint..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running"
    
    echo "📡 Testing /accounts endpoint:"
    RESPONSE=$(curl -s http://localhost:8000/accounts 2>&1)
    if echo "$RESPONSE" | grep -q '^\[.*\]$'; then
        echo "✅ API returned valid JSON array:"
        echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
        
        ACCOUNT_COUNT=$(echo "$RESPONSE" | jq length 2>/dev/null || echo "0")
        echo "📊 Account count: $ACCOUNT_COUNT"
    else
        echo "❌ API returned invalid response:"
        echo "$RESPONSE"
    fi
else
    echo "❌ Backend not running on http://localhost:8000"
    echo "💡 Start with: ./launch_expressdiff.sh"
fi
echo

# Test 3: Check SLURM environment
echo "3. Testing SLURM environment..."
if command -v sinfo &> /dev/null; then
    echo "✅ SLURM commands available"
    echo "🏗️ SLURM info:"
    sinfo | head -3
else
    echo "❌ SLURM commands not found"
fi

if [[ -n "$SLURM_JOB_ID" ]]; then
    echo "✅ Running in SLURM allocation: $SLURM_JOB_ID"
else
    echo "⚠️  Not running in SLURM allocation"
    echo "💡 For best results, start with: salloc -A <account> -p standard -c 4 --mem=16G -t 02:00:00"
fi
echo

# Test 4: Check alternative account methods
echo "4. Testing alternative account discovery..."
if command -v sacctmgr &> /dev/null; then
    echo "✅ sacctmgr command available"
    echo "🔍 User associations:"
    sacctmgr show associations user=$USER -n -P 2>/dev/null | head -5 | while IFS='|' read -r cluster account user partition qos; do
        [[ -n "$account" ]] && echo "  - $account"
    done
else
    echo "❌ sacctmgr command not available"
fi
echo

# Test 5: Frontend connectivity
echo "5. Testing frontend connectivity..."
if curl -f -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend not running on http://localhost:3000"
    echo "💡 Start with: ./launch_expressdiff.sh (option 3)"
fi
echo

echo "🎯 Troubleshooting Guide:"
echo "========================"
echo
echo "If accounts are greyed out:"
echo
echo "1. **Backend not running**"
echo "   Solution: ./launch_expressdiff.sh"
echo
echo "2. **Network/CORS issue**" 
echo "   - Check browser console (F12) for errors"
echo "   - Try refreshing the page"
echo
echo "3. **SLURM allocation issue**"
echo "   - Run: salloc -A <account> -p standard -c 4 --mem=16G -t 02:00:00"
echo "   - Then restart ExpressDiff"
echo
echo "4. **Account command failure**"
echo "   - Backend will use fallback accounts: default, general, standard"
echo "   - Check SLURM module is loaded"
echo
echo "5. **Permission issue**"
echo "   - Verify you have access to SLURM accounts"
echo "   - Contact HPC support if needed"
echo

echo "🧪 Quick Test:"
echo "=============="
echo "Try creating a run with 'default' account if available."
echo "If successful, the issue is just account discovery, not core functionality."