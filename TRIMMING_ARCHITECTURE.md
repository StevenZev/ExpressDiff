# Trimming Architecture - Complete Flow

## Directory Structure

### Run Creation
When a run is created via `POST /runs`:

```
BASE_DIR/runs/{run_id}/
├── raw/              # FASTQ files uploaded here
├── trimmed/          # Trimmed output
│   └── logs/         # Per-sample trim logs
├── qc_raw/           # FastQC on raw files
├── qc_trimmed/       # FastQC on trimmed files
├── star/             # STAR alignment output
│   └── logs/
├── featurecounts/    # Feature counting
│   └── logs/
├── counts/           # Count matrices
├── metadata/         # Sample metadata
├── de/               # Differential expression results
└── summaries/        # Summary reports
```

### File Upload
When files are uploaded via `POST /runs/{run_id}/upload`:

1. **FASTQ files** (`.fq.gz`, `.fastq.gz`) → `raw/` directory
2. **Reference files** (`.fa`, `.fasta`, `.gtf`) → `reference/` directory
3. **Metadata** (`.csv`, `.tsv`) → `metadata/` directory

**CRITICAL FIX**: Each destination directory is now created with `mkdir(parents=True, exist_ok=True)` before saving files.

## Trimming Workflow

### 1. Submit Trimming Stage
Endpoint: `POST /runs/{run_id}/stages/trim`

**Backend Flow:**
1. Load run state from `{BASE_DIR}/runs/{run_id}/run_state.json`
2. Get adapter type from run parameters (default: `NexteraPE-PE`)
3. Call `SLURMManager.submit_job()` with:
   - `stage="trim"`
   - `run_id`
   - `account` (SLURM account)
   - `adapter_type`

### 2. Script Generation
`SLURMScriptGenerator.generate_script()`:

1. **Read template** from: `{INSTALL_DIR}/slurm_templates/trim.slurm.template`
2. **Replace placeholders:**
   - `{RUN_ID}` → actual run UUID
   - `{ACCOUNT}` → SLURM account
   - `{BASE_DIR}` → work directory (e.g., `/home/user/Pipelinin/ExpressDiff` or `$SCRATCH/ExpressDiff`)
   - `{ADAPTER_TYPE}` → adapter type (e.g., `NexteraPE-PE`)
3. **Write generated script** to: `{BASE_DIR}/generated_slurm/trim_{run_id}.slurm`
4. **Make executable:** `chmod 755`

### 3. SLURM Execution
The generated script runs with these paths:

```bash
RUN_ID="{run_id}"
BASE_DIR="{BASE_DIR}"                          # e.g., /home/vth3bk/Pipelinin/ExpressDiff
RAW_DIR="${BASE_DIR}/runs/${RUN_ID}/raw"       # Input FASTQ files
TRIMMED_DIR="${BASE_DIR}/runs/${RUN_ID}/trimmed"  # Output directory
ADAPTER_TYPE="{ADAPTER_TYPE}"                  # e.g., NexteraPE-PE
```

**Key Operations:**
1. Create output directories (`trimmed/`, `trimmed/logs/`)
2. Load trimmomatic module
3. Find Trimmomatic command (either binary or JAR)
4. Find adapter file from module environment
5. Change to `RAW_DIR`
6. Find all forward files (`*_1.fq.gz`, `*_1.fastq.gz`)
7. For each forward file:
   - Generate reverse filename (`_1` → `_2`)
   - Extract sample name
   - Run Trimmomatic PE with:
     - Input: `{RAW_DIR}/{sample}_1.fq.gz` and `{RAW_DIR}/{sample}_2.fq.gz`
     - Output: `{TRIMMED_DIR}/{sample}_forward_paired.fq.gz`, etc.
     - Log: `{TRIMMED_DIR}/logs/{sample}_trim.log`
8. Track success/failure counts
9. Verify output files exist
10. Create completion flag: `{TRIMMED_DIR}/trimming_done.flag`

## Common Issues and Fixes

### Issue 1: "No such file or directory" for raw/
**Cause:** `raw/` directory not created before file upload
**Fix:** Added `dest_dir.mkdir(parents=True, exist_ok=True)` in upload endpoint

### Issue 2: Old test files persisting
**Cause:** Files uploaded to run persist independently of source changes
**Solution:** Create new run and upload corrected files

### Issue 3: Sequence/quality length mismatch
**Cause:** Malformed FASTQ files in test data
**Fix:** Corrected `create_test_data.sh` to ensure matching lengths

### Issue 4: Missing log directories
**Cause:** Script assumes `logs/` exists
**Fix:** 
- Backend creates `trimmed/logs/` during run creation
- Script also creates it with `mkdir -p`

### Issue 5: Complex script with functions and parallelism
**Cause:** Over-engineered script prone to errors
**Fix:** Rebuilt as simple sequential script with clear error handling

## File Path Summary

### Install Directory (Read-Only)
- `{INSTALL_DIR}/slurm_templates/trim.slurm.template` - Template source
- `{INSTALL_DIR}/trimAdapters4.slurm` - Legacy (not used anymore)

### Work Directory (User Writable)
- `{BASE_DIR}/runs/{run_id}/raw/*.fq.gz` - Input FASTQ files
- `{BASE_DIR}/runs/{run_id}/trimmed/*_paired.fq.gz` - Output trimmed files
- `{BASE_DIR}/runs/{run_id}/trimmed/logs/*.log` - Per-sample logs
- `{BASE_DIR}/runs/{run_id}/trimmed/trim_*.out` - SLURM stdout
- `{BASE_DIR}/runs/{run_id}/trimmed/trim_*.err` - SLURM stderr
- `{BASE_DIR}/runs/{run_id}/trimmed/trimming_done.flag` - Completion marker
- `{BASE_DIR}/generated_slurm/trim_{run_id}.slurm` - Generated script
- `{BASE_DIR}/runs/{run_id}/run_state.json` - Run state tracking

## Testing the Fix

1. **Restart backend** to pick up changes:
   ```bash
   bash launch_expressdiff.sh > backend.log 2>&1 &
   ```

2. **Create new run** in UI

3. **Upload corrected test files** from `test_data/`:
   - `sample_A_1.fq.gz`, `sample_A_2.fq.gz`
   - `sample_B_1.fq.gz`, `sample_B_2.fq.gz`

4. **Verify directory structure:**
   ```bash
   ls -la runs/{run_id}/raw/
   # Should show uploaded .fq.gz files
   ```

5. **Run QC** (optional)

6. **Submit trimming** stage

7. **Monitor output:**
   ```bash
   tail -f runs/{run_id}/trimmed/trim_*.out
   ```

Expected output:
- Clear headers showing run config
- "Found forward files" list
- Per-sample processing with ✓/✗
- Summary with success/fail counts
- "Created X paired output files"
- "✓ Trimming complete"
