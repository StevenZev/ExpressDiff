# Re-run Behavior in ExpressDiff

## Overview
ExpressDiff now implements **safe re-run protection** with user confirmation when attempting to re-run a previously completed pipeline stage.

## How It Works

### 1. **First Run**
- Stage executes normally
- Creates output files in the stage directory
- Creates a completion flag (e.g., `trimming_done.flag`, `star_done.flag`)

### 2. **Attempted Re-run**
When you try to submit a stage that has already completed:

1. **Backend detects completion** by checking for the completion flag
2. **Returns HTTP 409 (Conflict)** with message:
   ```
   Stage 'trim' was previously completed. 
   Re-running will delete previous results. 
   Set confirm_rerun=true to proceed.
   ```
3. **Frontend shows confirmation dialog**:
   ```
   ⚠️ Warning: Stage "trim" was previously completed.
   
   Re-running this stage will DELETE all previous results for this stage.
   
   Are you sure you want to proceed?
   ```

4. **User makes choice**:
   - **Cancel**: Nothing happens, previous results preserved
   - **OK**: Stage re-runs with cleanup

### 3. **Confirmed Re-run**
If user confirms:
1. **Cleanup runs first** - Removes all previous output files:
   - `trim`: Removes all `.fq.gz` files and completion flag
   - `star`: Removes `.bam`, `.tab`, `.out` files and completion flag
   - `qc_raw`/`qc_trimmed`: Removes all FastQC and MultiQC reports
   - `featurecounts`: Removes count files
   
2. **Stage executes fresh** - New outputs created
3. **New completion flag** created at the end

## Cleanup Details by Stage

### Trimming
```bash
rm -f ${TRIMMED_DIR}/*.fq.gz
rm -f ${TRIMMED_DIR}/trimming_done.flag
```
Removes: All trimmed FASTQ files

### STAR Alignment
```bash
rm -f $STAR_DIR/*.bam
rm -f $STAR_DIR/*.tab
rm -f $STAR_DIR/*_STARtmp
rm -f $STAR_DIR/*.out
rm -f $STAR_DIR/*.out.tab
rm -f $STAR_DIR/star_done.flag
```
Removes: BAM files, gene counts, STAR temporary files (keeps logs directory)

### QC (Raw and Trimmed)
```bash
rm -f $QC_OUT_DIR/fastqc_out/*
rm -f $QC_OUT_DIR/multiqc_out/*
rm -f $QC_OUT_DIR/qc_*_done.flag
```
Removes: All FastQC and MultiQC reports

### featureCounts
```bash
rm -f $COUNTS_DIR/*
```
Removes: All count files and summaries

## What's Preserved

During re-runs, the following are **NOT deleted**:
- Log files in `*/logs/` subdirectories
- Input files (raw uploads, trimmed reads for downstream stages)
- Other stage outputs (only the re-run stage is cleaned)

## API Usage

### Via Frontend
The UI handles this automatically with confirmation dialogs.

### Via API (Direct)
```python
import requests

# First attempt (will fail if completed)
response = requests.post(
    'http://localhost:8000/runs/{run_id}/stages/trim/submit',
    json={'account': 'my_account'}
)
# Returns 409 if already completed

# Confirmed re-run
response = requests.post(
    'http://localhost:8000/runs/{run_id}/stages/trim/submit',
    json={
        'account': 'my_account',
        'confirm_rerun': True  # Explicit confirmation
    }
)
# Proceeds with cleanup and re-run
```

## Design Rationale

**Why require confirmation?**
- Prevents accidental data loss
- Makes it explicit that previous results will be overwritten
- Gives users a chance to back up important results

**Why clean before run instead of archiving?**
- Simpler implementation
- Avoids disk space bloat from multiple runs
- Output directories have clear, current results
- Users can manually backup if needed before re-running

**Why clean everything in the stage?**
- Ensures no mixing of old and new results
- Prevents confusion from partial outputs
- Guarantees fresh, consistent results

## Best Practices

1. **Before re-running**, if you want to keep previous results:
   - Copy the stage directory: `cp -r runs/{run_id}/star runs/{run_id}/star_backup`
   - Or download important results via the UI

2. **Failed runs** that didn't complete don't trigger the confirmation:
   - Only completed runs (with completion flags) require confirmation
   - Failed runs can be re-submitted without confirmation

3. **Forced runs** still require re-run confirmation:
   - `force=true` bypasses dependency checks
   - `confirm_rerun=true` bypasses re-run protection
   - Both can be used together if needed
