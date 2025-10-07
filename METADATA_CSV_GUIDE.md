# DESeq2 Input Files Guide

## Required Input: metadata.csv

DESeq2 requires **ONE file**: `metadata.csv`

This file maps your samples to experimental conditions so DESeq2 knows which groups to compare.

---

## Basic Format (Demo Data)

**File**: `demo_metadata.csv` (already created for you!)

```csv
sample_name,condition
control_1,control
control_2,control
control_3,control
treatment_1,treatment
treatment_2,treatment
treatment_3,treatment
```

### Requirements:
- ✅ **Header row required**: First line must be `sample_name,condition`
- ✅ **sample_name column**: Must match your BAM file names (without `_Aligned.sortedByCoord.out.bam`)
- ✅ **condition column**: Your experimental groups (can be any names)
- ✅ **Minimum 2 conditions**: Need at least 2 groups to compare
- ✅ **Recommend ≥2 replicates** per condition for statistical power

---

## How to Find Your Sample Names

Your sample names come from your BAM files. Here's how to find them:

```bash
# Replace with your actual run ID
RUN_ID="your-run-id-here"

# List BAM files and extract sample names
ls /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/star/*.bam | \
  xargs -n1 basename | \
  sed 's/_Aligned.sortedByCoord.out.bam//'
```

**Example output:**
```
control_1
control_2
control_3
treatment_1
treatment_2
treatment_3
```

Use these **exact names** in your metadata.csv!

---

## Example Metadata Files

### Example 1: Control vs Treatment (Demo Data)
**Use case**: Compare gene expression between untreated and treated cells

```csv
sample_name,condition
control_1,control
control_2,control
control_3,control
treatment_1,treatment
treatment_2,treatment
treatment_3,treatment
```

**DESeq2 will compare**: treatment vs control (log2 fold change = treatment/control)

---

### Example 2: Wild-type vs Mutant
**Use case**: Compare gene expression between WT and knockout mice

```csv
sample_name,condition
WT_rep1,wildtype
WT_rep2,wildtype
WT_rep3,wildtype
KO_rep1,knockout
KO_rep2,knockout
KO_rep3,knockout
```

**DESeq2 will compare**: knockout vs wildtype

---

### Example 3: Multiple Cell Types
**Use case**: Compare 3 different cell types

```csv
sample_name,condition
neuron_1,neuron
neuron_2,neuron
neuron_3,neuron
astrocyte_1,astrocyte
astrocyte_2,astrocyte
astrocyte_3,astrocyte
microglia_1,microglia
microglia_2,microglia
microglia_3,microglia
```

**Note**: With >2 conditions, DESeq2 will currently compare treatment vs control. 
For pairwise comparisons, you'd need to run DESeq2 multiple times or modify the script.

---

### Example 4: Time Course (Advanced)
**Use case**: Gene expression at different time points

```csv
sample_name,condition,timepoint
ctrl_0h_1,control,0h
ctrl_0h_2,control,0h
ctrl_6h_1,control,6h
ctrl_6h_2,control,6h
treat_0h_1,treatment,0h
treat_0h_2,treatment,0h
treat_6h_1,treatment,6h
treat_6h_2,treatment,6h
```

**Note**: Currently only `condition` column is used. Additional columns are preserved but not used in the default analysis.

---

## Common Mistakes and How to Avoid Them

### ❌ Mistake 1: Sample Names Don't Match BAM Files
```csv
sample_name,condition
sample1,control    ← Wrong! Should match BAM filename exactly
sample2,control
```

**✅ Fix**: Use exact names from BAM files:
```bash
# Get correct names
ls /scratch/vth3bk/ExpressDiff/runs/RUN_ID/star/*.bam | \
  xargs -n1 basename | sed 's/_Aligned.sortedByCoord.out.bam//'
```

---

### ❌ Mistake 2: Missing Header Row
```csv
control_1,control    ← Missing header!
control_2,control
```

**✅ Fix**: Always start with header:
```csv
sample_name,condition
control_1,control
control_2,control
```

---

### ❌ Mistake 3: Wrong Column Names
```csv
sample,group         ← Wrong column names!
control_1,control
```

**✅ Fix**: Use exact column names:
```csv
sample_name,condition
control_1,control
```

---

### ❌ Mistake 4: Spaces in Values
```csv
sample_name,condition
control 1,control    ← Space in sample name!
```

**✅ Fix**: Use underscores, no spaces:
```csv
sample_name,condition
control_1,control
```

---

### ❌ Mistake 5: Only One Condition
```csv
sample_name,condition
sample_1,control
sample_2,control      ← All same condition, can't compare!
sample_3,control
```

**✅ Fix**: Need at least 2 conditions:
```csv
sample_name,condition
sample_1,control
sample_2,control
sample_3,treatment    ← Different condition
```

---

## Quick Validation Checklist

Before uploading your metadata.csv:

- [ ] File is named exactly `metadata.csv`
- [ ] First line is: `sample_name,condition`
- [ ] Sample names match BAM files exactly (check with `ls` command above)
- [ ] No spaces in sample names or conditions
- [ ] At least 2 different conditions
- [ ] Each condition has at least 2 samples (recommended)
- [ ] File is plain text CSV (not Excel .xlsx)
- [ ] No extra blank lines at the end

---

## How to Upload Metadata

### Option 1: Copy to Run Directory (Recommended)
```bash
# Replace with your actual run ID
RUN_ID="your-run-id-here"

# Create metadata directory
mkdir -p /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata

# Copy the demo metadata file
cp /home/vth3bk/Pipelinin/ExpressDiff/demo_metadata.csv \
   /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata/metadata.csv

# Verify it was copied
cat /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata/metadata.csv
```

### Option 2: Use the Helper Script
```bash
cd /home/vth3bk/Pipelinin/ExpressDiff
./create_demo_metadata.sh
# Enter your run ID when prompted
```

### Option 3: Create Custom Metadata
```bash
# Replace with your actual run ID
RUN_ID="your-run-id-here"

# Create custom metadata
cat > /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata/metadata.csv << 'EOF'
sample_name,condition
your_sample_1,control
your_sample_2,control
your_sample_3,treatment
your_sample_4,treatment
EOF
```

---

## Verify Metadata is Ready

```bash
RUN_ID="your-run-id-here"

# Check file exists
ls -lh /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata/metadata.csv

# View contents
cat /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata/metadata.csv

# Count samples (should be number of lines minus 1 for header)
wc -l /scratch/vth3bk/ExpressDiff/runs/${RUN_ID}/metadata/metadata.csv
```

Expected output:
```
-rw-r--r-- 1 vth3bk users 123 Oct  7 10:00 metadata.csv
sample_name,condition
control_1,control
control_2,control
control_3,control
treatment_1,treatment
treatment_2,treatment
treatment_3,treatment
7 /scratch/.../metadata/metadata.csv
```

---

## What Happens During DESeq2 Analysis

Once metadata.csv is uploaded, the DESeq2 stage will:

1. **Read counts.txt** from featureCounts (automatically)
2. **Read metadata.csv** (you provide this)
3. **Match samples** between counts and metadata
4. **Normalize counts** using DESeq2 size factors
5. **Test for differential expression** between conditions
6. **Generate result files**:
   - `full_results.csv` - All genes
   - `significant_degs.csv` - Significant genes (padj < 0.05, |log2FC| > 1)
   - `top_degs.csv` - Top 50 most significant
   - `summary.txt` - Statistics summary

---

## Template for Your Own Data

Copy and modify this template:

```csv
sample_name,condition
CHANGE_ME_1,control
CHANGE_ME_2,control
CHANGE_ME_3,control
CHANGE_ME_4,treatment
CHANGE_ME_5,treatment
CHANGE_ME_6,treatment
```

Replace `CHANGE_ME_X` with your actual sample names from the BAM files!

---

## Quick Reference

| What | Value |
|------|-------|
| **Filename** | `metadata.csv` |
| **Location** | `/scratch/vth3bk/ExpressDiff/runs/RUN_ID/metadata/` |
| **Required columns** | `sample_name`, `condition` |
| **Sample names** | Must match BAM filenames (without suffix) |
| **Minimum conditions** | 2 |
| **Recommended replicates** | ≥2 per condition |
| **Format** | Plain text CSV |
| **Encoding** | UTF-8 |

---

## Need Help?

1. **Find your sample names**:
   ```bash
   ./find_runs.sh
   ```

2. **Create demo metadata**:
   ```bash
   ./create_demo_metadata.sh
   ```

3. **Validate existing metadata**:
   ```bash
   cat /scratch/vth3bk/ExpressDiff/runs/RUN_ID/metadata/metadata.csv
   ```

4. **Check full documentation**:
   - `TEST_DESEQ2.md` - Testing guide
   - `DESEQ2_IMPLEMENTATION.md` - Technical details
