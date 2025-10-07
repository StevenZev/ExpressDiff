# STAR Template - Path and Logging Improvements

## Changes Made

### 1. **Fixed SLURM Output Paths**
**Before:**
```bash
#SBATCH --output=./runs/{RUN_ID}/star/star_%j.out
#SBATCH --error=./runs/{RUN_ID}/star/star_%j.err
```

**After:**
```bash
#SBATCH --output={BASE_DIR}/runs/{RUN_ID}/star/logs/star_%j.out
#SBATCH --error={BASE_DIR}/runs/{RUN_ID}/star/logs/star_%j.err
```

**Why:** 
- ✅ Uses absolute paths (not relative `.` which can fail)
- ✅ Logs go to dedicated `logs/` subdirectory
- ✅ Consistent with trim template structure

---

### 2. **Added BASE_DIR Variable**
**Before:**
```bash
RUN_DIR="./runs/$RUN_ID"
cd {BASE_DIR}
```

**After:**
```bash
BASE_DIR="{BASE_DIR}"
RUN_DIR="$BASE_DIR/runs/$RUN_ID"
# No cd command - all paths are absolute
```

**Why:**
- ✅ All paths are absolute from the start
- ✅ No dependency on current working directory
- ✅ More reliable in SLURM environment

---

### 3. **Created Dedicated Logs Directory**
**New:**
```bash
LOGS_DIR="$STAR_DIR/logs"
mkdir -p "$LOGS_DIR"
```

**Files written to logs/**:
- `star_{JOB_ID}.out` - SLURM stdout
- `star_{JOB_ID}.err` - SLURM stderr
- `genome_index_build.log` - Index generation output
- `{sample}_alignment.log` - Per-sample alignment output

**Why:**
- ✅ Organized logging structure
- ✅ Easy to find all logs in one place
- ✅ Separates logs from output data

---

### 4. **Enhanced Error Messages**
**Improvements:**

**Reference Files:**
```bash
# Now shows exactly what was searched and found
echo "Searching for reference files..."
echo "  Checking run-specific reference: $REFERENCE_DIR"
echo "    Found FASTA: test_genome.fa"
echo "  Using reference files:"
echo "    FASTA: /scratch/.../reference/test_genome.fa"
echo "    GTF: /scratch/.../reference/test_annotation.gtf"
```

**Input Files:**
```bash
echo "Checking for trimmed FASTQ files..."
echo "  Forward paired files: 3"
echo "  Reverse paired files: 3"
echo ""
echo "Found trimmed files:"
echo "  sample_A_forward_paired.fq.gz"
echo "  sample_B_forward_paired.fq.gz"
echo "  sample_C_forward_paired.fq.gz"
```

---

### 5. **Added Per-Sample Logging**
**New feature:**
```bash
align_sample() {
    local log_prefix="$LOGS_DIR/${basename}"
    
    STAR ... 2>&1 | tee "${log_prefix}_alignment.log"
}
```

**Creates:**
- `logs/sample_A_alignment.log`
- `logs/sample_B_alignment.log`
- `logs/sample_C_alignment.log`

**Why:**
- ✅ Can debug individual sample failures
- ✅ See full STAR output per sample
- ✅ Preserved even after job completes

---

### 6. **Better Progress Reporting**
**Added throughout:**
```bash
echo "=== STAR Alignment for RNA-seq ==="
echo "Run ID: $RUN_ID"
echo "Base directory: $BASE_DIR"
echo "Input directory: $TRIMMED_DIR"
echo "Output directory: $STAR_DIR"
echo "Logs directory: $LOGS_DIR"
echo ""
echo "Loading modules..."
echo "  STAR version: STAR_2.7.10b"
echo ""
echo "Checking for STAR genome index..."
echo "  Index not found, building now..."
echo "  ✓ Genome index built successfully"
echo ""
echo "=== Starting parallel alignment ==="
echo "Parallel jobs: 4"
echo "=== Aligning sample: sample_A ==="
echo "  ✓ Alignment complete for sample_A"
echo ""
echo "=== Alignment Summary ==="
echo "Successful: 3"
echo "Failed: 0"
```

---

### 7. **Sequential Processing Instead of GNU Parallel**
**Before:**
```bash
find "$TRIMMED_DIR" -name "*_forward_paired.fq.gz" | \
    parallel -j $((SLURM_CPUS_PER_TASK/2)) --halt now,fail=1 \
    align_sample {}
```

**After:**
```bash
while IFS= read -r fwd_file; do
    if align_sample "$fwd_file"; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
    fi
done < <(find "$TRIMMED_DIR" -name "*_forward_paired.fq.gz")
```

**Why:**
- ✅ Better error tracking per sample
- ✅ Clearer logging output (not interleaved)
- ✅ Can continue processing even if one sample fails
- ⚠️ Slower (sequential), but more reliable for small sample counts

**Note:** For production with many samples, can revert to parallel with proper logging

---

### 8. **Output Verification**
**New check at end:**
```bash
echo "Checking output files..."
BAM_COUNT=$(ls "$STAR_DIR"/*_Aligned.sortedByCoord.out.bam 2>/dev/null | wc -l)
COUNT_COUNT=$(ls "$STAR_DIR"/*_ReadsPerGene.out.tab 2>/dev/null | wc -l)

echo "  BAM files: $BAM_COUNT"
echo "  Count files: $COUNT_COUNT"

if [ "$BAM_COUNT" -eq 0 ]; then
    echo "ERROR: No BAM files were created"
    exit 1
fi
```

**Why:**
- ✅ Validates alignment actually produced output
- ✅ Fails job if no BAM files created
- ✅ Shows counts for verification

---

## Directory Structure After Run

```
/scratch/vth3bk/ExpressDiff/runs/{RUN_ID}/
└── star/
    ├── logs/                                    # NEW - All logs here
    │   ├── star_4567890.out                    # SLURM stdout
    │   ├── star_4567890.err                    # SLURM stderr
    │   ├── genome_index_build.log              # Index build output
    │   ├── sample_A_alignment.log              # Per-sample logs
    │   ├── sample_B_alignment.log
    │   └── sample_C_alignment.log
    ├── genome_index/                            # STAR index
    │   ├── SA
    │   ├── SAindex
    │   └── ...
    ├── sample_A_Aligned.sortedByCoord.out.bam  # Alignment output
    ├── sample_A_ReadsPerGene.out.tab           # Gene counts
    ├── sample_A_Log.final.out                  # Alignment stats
    ├── sample_A_Log.out
    ├── sample_A_Log.progress.out
    ├── sample_B_...
    ├── sample_C_...
    └── star_alignment_done.flag                # Completion marker
```

---

## Debugging Guide

### Where to Look When Things Fail

1. **Job didn't start:**
   - Check: `star/logs/star_{JOB_ID}.err`
   - Look for: SLURM errors, missing directories, permission issues

2. **Index build failed:**
   - Check: `star/logs/genome_index_build.log`
   - Look for: Reference file errors, memory issues, GTF format problems

3. **Sample alignment failed:**
   - Check: `star/logs/{sample}_alignment.log`
   - Look for: FASTQ format errors, memory issues, read errors

4. **Job completed but no output:**
   - Check: `star/logs/star_{JOB_ID}.out`
   - Look for: "ERROR: No BAM files were created"
   - Verify: Input files exist in trimmed/

### Common Issues

**"Trimmed directory not found":**
```bash
# Check if trimming completed
ls /scratch/vth3bk/ExpressDiff/runs/{RUN_ID}/trimmed/
# Should see *_forward_paired.fq.gz and *_reverse_paired.fq.gz
```

**"No reference files found":**
```bash
# Check run-specific reference
ls /scratch/vth3bk/ExpressDiff/runs/{RUN_ID}/reference/

# Check global reference
ls /scratch/vth3bk/ExpressDiff/mapping_in/
```

**"Memory allocation failed":**
```
# Index build needs ~32GB RAM minimum
# Alignment needs ~32GB for human, ~16GB for mouse
# Job requests 64GB which should be sufficient
```

---

## Testing

After changes, test with:

```bash
# Verify paths in generated script
RUN_ID="550190eb-8233-49c7-844b-48caab4dc3f3"
python3 << EOF
from backend.core.script_generator import SLURMScriptGenerator
gen = SLURMScriptGenerator()
script_path = gen.generate_script('star', '$RUN_ID', 'standard')
print(f"Generated: {script_path}")

# Check paths in script
with open(script_path) as f:
    for i, line in enumerate(f, 1):
        if 'SBATCH' in line or 'DIR=' in line:
            print(f"{i:3}: {line.rstrip()}")
EOF
```

---

## Benefits

✅ **Absolute paths** - No more relative path issues
✅ **Organized logs** - All logs in one `logs/` directory
✅ **Better debugging** - Per-sample logs, detailed error messages
✅ **Verification** - Checks output files were created
✅ **Progress tracking** - Clear status messages throughout
✅ **Error handling** - Graceful failure with useful messages

