#!/bin/bash
# Test ExpressDiff is running correctly from FastX

echo "=== ExpressDiff Runtime Tests ==="
echo

# 1. Check backend is running
echo "1. Checking if backend is running..."
BACKEND_PID=$(ps aux | grep "[u]vicorn.*backend.api.main" | awk '{print $2}')
if [ -n "$BACKEND_PID" ]; then
    echo "   ✓ Backend is running (PID: $BACKEND_PID)"
    ps aux | grep "[u]vicorn.*backend.api.main" | head -1
else
    echo "   ✗ Backend is NOT running!"
    exit 1
fi
echo

# 2. Check what directory backend is running from
echo "2. Checking backend working directory..."
if [ -n "$BACKEND_PID" ]; then
    BACKEND_CWD=$(readlink -f /proc/$BACKEND_PID/cwd 2>/dev/null)
    if [ -n "$BACKEND_CWD" ]; then
        echo "   Working directory: $BACKEND_CWD"
        if [[ "$BACKEND_CWD" == *"Pipelinin/ExpressDiff"* ]]; then
            echo "   ✓ Running from correct location (Pipelinin)"
        else
            echo "   ⚠ Running from: $BACKEND_CWD"
            echo "   Expected: /home/vth3bk/Pipelinin/ExpressDiff"
        fi
    fi
fi
echo

# 3. Test API health endpoint
echo "3. Testing API health endpoint..."
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ✓ API responding"
    echo "   Response: $HEALTH"
else
    echo "   ✗ API not responding on localhost:8000"
    echo "   Try: curl http://localhost:8000/health"
fi
echo

# 4. Test storage info endpoint
echo "4. Testing storage configuration..."
STORAGE=$(curl -s http://localhost:8000/storage-info 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ✓ Storage endpoint responding"
    echo "$STORAGE" | python3 -m json.tool 2>/dev/null || echo "   $STORAGE"
    
    # Check if using scratch
    if echo "$STORAGE" | grep -q "scratch"; then
        echo "   ✓ Using scratch storage"
    else
        echo "   ⚠ Not using scratch storage"
    fi
else
    echo "   ✗ Storage endpoint not responding"
fi
echo

# 5. Check SLURM accounts
echo "5. Testing SLURM accounts endpoint..."
ACCOUNTS=$(curl -s http://localhost:8000/accounts 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ✓ Accounts endpoint responding"
    echo "   Available accounts: $ACCOUNTS"
else
    echo "   ✗ Accounts endpoint not responding"
fi
echo

# 6. Check template files are accessible
echo "6. Verifying template files..."
BACKEND_DIR=$(readlink -f /proc/$BACKEND_PID/cwd 2>/dev/null || echo "/home/vth3bk/Pipelinin/ExpressDiff")
if [ -f "$BACKEND_DIR/slurm_templates/trim.slurm.template" ]; then
    TEMPLATE_SIZE=$(wc -l < "$BACKEND_DIR/slurm_templates/trim.slurm.template")
    echo "   ✓ Trim template found ($TEMPLATE_SIZE lines)"
    
    # Check for new template indicators
    if grep -q "=== Trimmomatic Adapter Trimming ===" "$BACKEND_DIR/slurm_templates/trim.slurm.template"; then
        echo "   ✓ Using NEW rebuilt template"
    else
        echo "   ⚠ Template may be outdated"
    fi
else
    echo "   ✗ Template not found at $BACKEND_DIR/slurm_templates/"
fi
echo

# 7. Check scratch directory
echo "7. Checking scratch storage..."
if [ -d "/scratch/$USER/ExpressDiff" ]; then
    echo "   ✓ Scratch directory exists: /scratch/$USER/ExpressDiff"
    echo "   Current runs:"
    ls -1 /scratch/$USER/ExpressDiff/runs/ 2>/dev/null | head -5 || echo "     (no runs yet)"
else
    echo "   ⚠ Scratch directory not created yet"
    echo "     Will be created when first run is made"
fi
echo

# 8. Check frontend (if running)
echo "8. Checking frontend..."
FRONTEND_PID=$(ps aux | grep "[n]pm.*start" | grep -v grep | awk '{print $2}')
if [ -n "$FRONTEND_PID" ]; then
    echo "   ✓ Frontend is running (PID: $FRONTEND_PID)"
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "   ✓ Frontend responding on port 3000"
    else
        echo "   ⚠ Frontend process running but not responding yet"
    fi
else
    echo "   ℹ Frontend not running (backend only mode)"
fi
echo

# 9. Show backend logs (last 20 lines)
echo "9. Recent backend logs:"
if [ -f "backend.log" ]; then
    echo "   --- Last 20 lines of backend.log ---"
    tail -20 backend.log
else
    echo "   ℹ No backend.log file found"
    echo "   Check terminal output or redirect to log file"
fi
echo

# Summary
echo "=== Test Summary ==="
echo "✓ Backend running from: $BACKEND_CWD"
echo "✓ API available at: http://localhost:8000"
echo "✓ API docs at: http://localhost:8000/docs"
if [ -n "$FRONTEND_PID" ]; then
    echo "✓ Frontend at: http://localhost:3000"
fi
echo
echo "Next steps:"
echo "1. Open the UI in your browser"
echo "2. Create a new run"
echo "3. Upload test files from: /home/vth3bk/Pipelinin/ExpressDiff/test_data/"
echo "4. Monitor with: tail -f /scratch/$USER/ExpressDiff/runs/{run_id}/trimmed/trim_*.out"
