#!/bin/bash
# find_runs.sh
# Helper script to list available runs and check their status

echo "==============================================="
echo "ExpressDiff Runs Summary"
echo "==============================================="
echo ""

RUNS_DIR="/scratch/vth3bk/ExpressDiff/runs"

if [ ! -d "$RUNS_DIR" ]; then
    echo "No runs directory found at $RUNS_DIR"
    exit 1
fi

echo "Available runs:"
echo ""

for run_dir in "$RUNS_DIR"/*; do
    if [ -d "$run_dir" ]; then
        RUN_ID=$(basename "$run_dir")
        
        # Check stage completion
        HAS_QC_RAW="❌"
        HAS_TRIM="❌"
        HAS_STAR="❌"
        HAS_FEATURECOUNTS="❌"
        HAS_METADATA="❌"
        HAS_DESEQ="❌"
        
        [ -f "$run_dir/qc_raw/qc_raw_done.flag" ] && HAS_QC_RAW="✅"
        [ -f "$run_dir/trimmed/trimming_done.flag" ] && HAS_TRIM="✅"
        [ -f "$run_dir/star/star_alignment_done.flag" ] && HAS_STAR="✅"
        [ -f "$run_dir/featurecounts/featurecounts_done.flag" ] && HAS_FEATURECOUNTS="✅"
        [ -f "$run_dir/metadata/metadata.csv" ] && HAS_METADATA="✅"
        [ -f "$run_dir/logs/deseq2_done.flag" ] && HAS_DESEQ="✅"
        
        # Count samples
        SAMPLE_COUNT=0
        if [ -d "$run_dir/raw" ]; then
            SAMPLE_COUNT=$(ls "$run_dir/raw"/*_1.fq.gz 2>/dev/null | wc -l)
        fi
        
        echo "───────────────────────────────────────────────"
        echo "RUN ID: $RUN_ID"
        echo "Samples: $SAMPLE_COUNT"
        echo "Stages:"
        echo "  QC Raw:        $HAS_QC_RAW"
        echo "  Trim:          $HAS_TRIM"
        echo "  STAR:          $HAS_STAR"
        echo "  featureCounts: $HAS_FEATURECOUNTS"
        echo "  Metadata:      $HAS_METADATA"
        echo "  DESeq2:        $HAS_DESEQ"
        
        # Show readiness for DESeq2
        if [ "$HAS_FEATURECOUNTS" = "✅" ] && [ "$HAS_METADATA" = "✅" ] && [ "$HAS_DESEQ" = "❌" ]; then
            echo ""
            echo "  🎯 READY FOR DESEQ2!"
        elif [ "$HAS_FEATURECOUNTS" = "✅" ] && [ "$HAS_METADATA" = "❌" ]; then
            echo ""
            echo "  ⚠️  NEEDS METADATA - run: ./create_demo_metadata.sh"
        elif [ "$HAS_DESEQ" = "✅" ]; then
            echo ""
            echo "  ✓  DESeq2 completed"
        fi
        
        echo ""
    fi
done

echo "==============================================="
echo ""
echo "To create metadata for a run:"
echo "  ./create_demo_metadata.sh"
echo ""
echo "To run DESeq2:"
echo "  1. Create metadata (if needed)"
echo "  2. Open run in UI"
echo "  3. Go to Pipeline tab"
echo "  4. Click Run on DESeq2 Analysis"
echo ""
echo "To view results:"
echo "  ls /scratch/vth3bk/ExpressDiff/runs/RUN_ID/deseq2/"
