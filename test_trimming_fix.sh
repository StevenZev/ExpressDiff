#!/bin/bash
# Test script to verify trimming architecture fixes

set -e

echo "=== Testing Trimming Architecture Fixes ==="
echo

# Check if backend is running
echo "1. Checking backend status..."
if pgrep -f "uvicorn.*expressdiff" > /dev/null; then
    echo "   ✓ Backend is running"
else
    echo "   ✗ Backend not running - start with: bash launch_expressdiff.sh > backend.log 2>&1 &"
    exit 1
fi
echo

# Check template exists
echo "2. Checking template file..."
if [ -f "slurm_templates/trim.slurm.template" ]; then
    echo "   ✓ Template exists"
    echo "   Size: $(wc -l < slurm_templates/trim.slurm.template) lines"
else
    echo "   ✗ Template not found"
    exit 1
fi
echo

# Check test data
echo "3. Checking test data..."
if [ -d "test_data" ] && [ -f "test_data/sample_A_1.fq.gz" ]; then
    echo "   ✓ Test data exists"
    echo "   Files:"
    ls -lh test_data/*.fq.gz | awk '{print "     ", $9, "("$5")"}'
else
    echo "   ✗ Test data not found - regenerate with: bash create_test_data.sh"
    exit 1
fi
echo

# Verify test data format
echo "4. Verifying test data format..."
for file in test_data/sample_A_*.fq.gz; do
    sample=$(basename "$file" .fq.gz)
    
    # Get first read
    read_data=$(zcat "$file" | head -4)
    seq_line=$(echo "$read_data" | sed -n '2p')
    qual_line=$(echo "$read_data" | sed -n '4p')
    seq_len=${#seq_line}
    qual_len=${#qual_line}
    
    if [ "$seq_len" -eq "$qual_len" ]; then
        echo "   ✓ $sample: sequence=$seq_len, quality=$qual_len (match)"
    else
        echo "   ✗ $sample: sequence=$seq_len, quality=$qual_len (MISMATCH)"
        exit 1
    fi
done
echo

# Check API connectivity
echo "5. Testing API connectivity..."
API_URL="http://localhost:8000"
if curl -s "${API_URL}/health" > /dev/null; then
    echo "   ✓ API responding at ${API_URL}"
else
    echo "   ✗ API not responding - check backend.log"
    exit 1
fi
echo

# List accounts
echo "6. Checking SLURM accounts..."
accounts=$(curl -s "${API_URL}/accounts")
if [ -n "$accounts" ] && [ "$accounts" != "[]" ]; then
    echo "   ✓ Accounts available:"
    echo "     $accounts"
else
    echo "   ⚠ No accounts found (may use fallback)"
fi
echo

echo "=== All Checks Passed! ==="
echo
echo "Next steps:"
echo "1. Create a new run in the UI"
echo "2. Upload files from test_data/ directory:"
echo "   - sample_A_1.fq.gz, sample_A_2.fq.gz"
echo "   - sample_B_1.fq.gz, sample_B_2.fq.gz"
echo "3. Run QC (optional)"
echo "4. Submit trimming stage"
echo "5. Monitor: tail -f runs/{run_id}/trimmed/trim_*.out"
echo
echo "The trimming should now work correctly with:"
echo "  - Proper directory structure (raw/ created on upload)"
echo "  - Corrected FASTQ format (matching seq/qual lengths)"
echo "  - Rebuilt simple script (clear error handling)"
