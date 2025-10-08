#!/bin/bash
# create_demo_metadata.sh
# Quick script to create metadata.csv for demo data

cat << 'EOF'
===============================================
Demo Data Metadata Generator
===============================================

This script will create metadata.csv for the
demo RNA-seq data (3 control + 3 treatment).
EOF

# Get run ID from user
echo ""
read -p "Enter your run ID (or press Enter to just generate the file): " RUN_ID

# Create metadata file
echo ""
echo "Creating metadata.csv..."

cat > metadata.csv << 'METADATA'
sample_name,condition
control_1,control
control_2,control
control_3,control
treatment_1,treatment
treatment_2,treatment
treatment_3,treatment
METADATA

echo "✓ Created metadata.csv"
cat metadata.csv
echo ""

# If run ID provided, copy to run directory
if [ -n "$RUN_ID" ]; then
    RUN_DIR="/scratch/vth3bk/ExpressDiff/runs/${RUN_ID}"
    
    if [ ! -d "$RUN_DIR" ]; then
        echo "⚠ Warning: Run directory not found: $RUN_DIR"
        echo "File created as ./metadata.csv"
        echo "You can manually copy it later."
    else
        echo "Copying to run directory..."
        mkdir -p "${RUN_DIR}/metadata"
        cp metadata.csv "${RUN_DIR}/metadata/metadata.csv"
        echo "✓ Copied to ${RUN_DIR}/metadata/metadata.csv"
        echo ""
        echo "Verifying:"
        cat "${RUN_DIR}/metadata/metadata.csv"
        echo ""
        echo "✓ Ready to run DESeq2!"
    fi
else
    echo "File created as ./metadata.csv"
    echo ""
    echo "To upload later, use:"
    echo "  RUN_ID='your-run-id'"
    echo "  mkdir -p /scratch/vth3bk/ExpressDiff/runs/\${RUN_ID}/metadata"
    echo "  cp metadata.csv /scratch/vth3bk/ExpressDiff/runs/\${RUN_ID}/metadata/"
fi

echo ""
echo "Next steps:"
echo "1. Go to ExpressDiff UI"
echo "2. Open your run"
echo "3. Click 'Pipeline' tab"
echo "4. Click 'Run' on 'DESeq2 Analysis' stage"
echo "5. Select SLURM account and submit"
