# Testing DESeq2 Functionality - Quick Start Guide

## Prerequisites

Before running DESeq2, you need:

1. ✅ **Completed featureCounts stage** - generates `counts.txt`
2. ✅ **Uploaded metadata.csv** - defines experimental conditions

## Step 1: Create metadata.csv

For your demo data (6 samples: 3 control + 3 treatment), create this file:

```csv
sample_name,condition
control_1,control
control_2,control
control_3,control
treatment_1,treatment
treatment_2,treatment
treatment_3,treatment
```

**Important Notes:**
- `sample_name` must match the BAM file names (without `_Aligned.sortedByCoord.out.bam`)
- Column names `sample_name` and `condition` are **required**
- Condition names are case-sensitive but can be anything (e.g., "wt"/"mutant", "untreated"/"treated")

## Step 2: Upload metadata.csv

### Option A: Through UI (if metadata upload is implemented)
1. Go to your run
2. Click "Files" tab
3. Upload `metadata.csv`

### Option B: Manual Upload (Recommended for testing)
```bash
# Replace RUN_ID with your actual run ID
RUN_ID="your-run-id-here"

# Create metadata file
cat > /tmp/metadata.csv << 'EOF'
sample_name,condition
control_1,control
control_2,control
control_3,control
treatment_1,treatment
treatment_2,treatment
treatment_3,treatment
EOF

# Create metadata directory if it doesn't exist
mkdir -p /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata

# Copy metadata file
cp /tmp/metadata.csv /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata/metadata.csv

# Verify it's there
cat /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata/metadata.csv
```

## Step 3: Run DESeq2 from Frontend

1. **Open your run** in the UI
2. **Click "Pipeline" tab** (not "Results")
3. **Scroll down** to see all pipeline stages:
   ```
   ✓ QC Raw
   ✓ Trim Adapters
   ✓ QC Trimmed
   ✓ STAR Alignment
   ✓ Count Features
   ⏸ DESeq2 Analysis  ← This one!
   ```

4. **Click "Run"** on the "DESeq2 Analysis" stage
5. **Select your SLURM account** from dropdown
6. **Click "Submit"**

## Step 4: Monitor Progress

### In the UI:
- Stage status will change: Pending → Running → Completed
- Refresh button available if status doesn't auto-update

### In Terminal:
```bash
# Check job status
squeue -u $USER

# Watch live logs
RUN_ID="your-run-id-here"
tail -f /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/logs/deseq2_*.out
```

Expected runtime: ~5-10 minutes for demo data

## Step 5: Check Results

### Output Location:
```bash
RUN_ID="your-run-id-here"
ls -lh /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/deseq2/
```

### Expected Files:
```
deseq2/
├── counts_matrix.csv          # Processed counts matrix
├── full_results.csv           # All genes with statistics
├── significant_degs.csv       # Filtered: padj<0.05, |log2FC|>1
├── top_degs.csv              # Top 50 most significant
├── summary.txt               # Summary statistics
└── run_deseq2.py            # Generated Python script
```

### View Results:
```bash
# Summary
cat /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/deseq2/summary.txt

# Top DEGs
head -20 /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/deseq2/top_degs.csv

# Count significant DEGs
wc -l /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/deseq2/significant_degs.csv
```

### Expected Results (Demo Data):
- **~20 significant DEGs**: 10 upregulated, 10 downregulated
- These match the synthetic genes created with differential expression
- ~100 total genes analyzed

## Troubleshooting

### Error: "Metadata file not found"
**Cause**: metadata.csv not uploaded or in wrong location

**Fix**:
```bash
# Check if file exists
RUN_ID="your-run-id-here"
ls -lh /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata/

# If missing, create and upload using Step 2 above
```

### Error: "featureCounts output not found"
**Cause**: featureCounts stage not completed

**Fix**:
1. Go to Pipeline tab
2. Ensure "Count Features" stage shows "Completed"
3. Verify counts.txt exists:
   ```bash
   ls -lh /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/featurecounts/counts.txt
   ```

### Error: "Sample names don't match"
**Cause**: metadata.csv sample names don't match BAM file names

**Fix**:
```bash
# List actual sample names from BAM files
RUN_ID="your-run-id-here"
ls /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/star/*_Aligned.sortedByCoord.out.bam | \
  xargs -n1 basename | sed 's/_Aligned.sortedByCoord.out.bam//'

# Update metadata.csv to use these exact names
```

### Error: "conda environment not found"
**Cause**: testenv not available or pydeseq2 not installed

**Fix**:
```bash
# Check conda environment
module load miniforge
conda env list

# Check pydeseq2
conda activate testenv
conda list | grep pydeseq2

# If missing, install:
conda install -c conda-forge pydeseq2
```

### Job Stuck in "Pending"
**Cause**: SLURM queue busy or account issues

**Check**:
```bash
# Check job status
squeue -u $USER

# Check account balance
allocations
```

### No Significant DEGs Found
**Cause**: 
- Real data with no differential expression
- Test data with insufficient alignment

**For Demo Data**:
- Should find ~20 DEGs
- If 0 found, check alignment rates in STAR logs
- Verify featureCounts assigned reads to genes

## Testing Checklist

- [ ] metadata.csv created with correct format
- [ ] metadata.csv uploaded to run directory
- [ ] featureCounts stage completed successfully
- [ ] featureCounts generated counts.txt file
- [ ] DESeq2 stage appears in frontend Pipeline tab
- [ ] Can select SLURM account and submit job
- [ ] Job runs without errors
- [ ] Results files created in deseq2/ directory
- [ ] Top DEGs file contains expected genes (for demo data)

## Quick Test with Real Run

If you have a completed run with featureCounts done:

```bash
# 1. Find a completed run
ls /scratch/vth3bk/ExpressDiff/runs/

# 2. Pick one and check featureCounts
RUN_ID="550190eb-8233-49c7-844b-48caab4dc3f3"  # Example
ls /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/featurecounts/counts.txt

# 3. Get actual sample names
ls /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/star/*.bam | \
  xargs -n1 basename | sed 's/_Aligned.sortedByCoord.out.bam//'

# 4. Create metadata (adjust names as needed)
mkdir -p /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata
cat > /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata/metadata.csv << 'EOF'
sample_name,condition
sample_A,control
sample_B,treatment
sample_C,treatment
EOF

# 5. Submit via UI (or test directly)
# Go to UI → Run → Pipeline → DESeq2 Analysis → Run
```

## Next Steps After Testing

Once DESeq2 works:
1. ✅ Test with demo data
2. ✅ Test with real RNA-seq data
3. 🔄 Build Metadata Builder UI (makes Step 1-2 automatic)
4. 🔄 Add DESeq2 results visualization
5. 🔄 Display results in UI Results tab

## UI Screenshot Guide

When testing in UI, you should see:

```
┌─────────────────────────────────────────────────┐
│ Pipeline Stages                                 │
├─────────────────────────────────────────────────┤
│ ✓ QC Raw                           [View Logs]  │
│ ✓ Trim Adapters                    [View Logs]  │
│ ✓ QC Trimmed                       [View Logs]  │
│ ✓ STAR Alignment                   [View Logs]  │
│ ✓ Count Features                   [View Logs]  │
│ ⏸ DESeq2 Analysis         [Run]   [View Logs]  │
│   Differential expression analysis              │
│   (requires metadata.csv)                       │
└─────────────────────────────────────────────────┘
```

After clicking Run and submitting:
```
⏳ DESeq2 Analysis      [Pending]   [View Logs]
   Job ID: 12345678

↓ (after ~1 min)

🔄 DESeq2 Analysis      [Running]   [View Logs]
   Job ID: 12345678

↓ (after ~5-10 min)

✓ DESeq2 Analysis     [Completed]  [View Logs]
   Job ID: 12345678
```
