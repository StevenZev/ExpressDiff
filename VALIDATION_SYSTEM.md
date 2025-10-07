# Stage Validation System - Implementation Summary

## Overview
Added comprehensive pre-submission validation to catch missing files and configuration issues before submitting SLURM jobs.

---

## Backend Changes

### New Endpoint: `GET /runs/{run_id}/stages/{stage}/validate`

**Returns:**
```json
{
  "valid": true/false,
  "errors": ["error1", "error2", ...],
  "warnings": ["warning1", "warning2", ...],
  "stage": "stage_name",
  "run_id": "run_id"
}
```

### Stage-Specific Validations

#### **QC Raw**
- ✅ Checks raw data directory exists
- ✅ Verifies FASTQ files present (.fq.gz or .fastq.gz)
- ⚠️ Warns if file count is odd (expects pairs)

#### **Trim**
- ✅ Checks raw FASTQ files exist
- ⚠️ Warns if adapter type not specified (uses default)

#### **QC Trimmed**
- ✅ Checks trimmed directory exists
- ✅ Verifies trimmed paired files exist (*_paired.fq.gz)

#### **STAR Alignment**
- ✅ Checks trimmed paired files exist (forward & reverse)
- ✅ Validates forward/reverse file count matches
- ✅ **Checks for reference FASTA file (.fa or .fasta)**
  - First in: `runs/{RUN_ID}/reference/`
  - Then in: `mapping_in/` (global)
- ✅ **Checks for annotation GTF file (.gtf)**
  - First in: `runs/{RUN_ID}/reference/`
  - Then in: `mapping_in/` (global)

#### **featureCounts**
- ✅ Checks STAR output BAM files exist
- ✅ Verifies GTF annotation file available

#### **All Stages**
- ✅ Validates dependencies completed
- ✅ Prevents submission if validation fails (unless forced)

---

## Frontend Changes

### Updated Files
1. **`frontend/src/api/client.ts`**
   - Added `StageValidation` interface
   - Added `validateStage()` API method

2. **`frontend/src/components/StageControls.tsx`**
   - Modified `submitStage()` to call validation first
   - Shows validation errors in Alert with bullet points
   - Improved error display with `whiteSpace: 'pre-line'` for multi-line errors

### User Experience
When user clicks a stage submit button:

1. **Validation runs automatically** (no extra click needed)
2. **If valid:** Job submits immediately
3. **If invalid:** Shows clear error message:
   ```
   Cannot submit STAR Alignment:
   • No forward paired FASTQ files found in trimmed directory
   • No reference genome FASTA file (.fa or .fasta) found
   • No gene annotation GTF file (.gtf) found
   ```

---

## Example Validation Scenarios

### ✅ **Success Case - STAR with all files**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "stage": "star",
  "run_id": "abc123"
}
```
→ Job submits immediately

### ❌ **Error Case - STAR missing reference**
```json
{
  "valid": false,
  "errors": [
    "No reference genome FASTA file (.fa or .fasta) found in reference/ or mapping_in/",
    "No gene annotation GTF file (.gtf) found in reference/ or mapping_in/"
  ],
  "warnings": [],
  "stage": "star",
  "run_id": "abc123"
}
```
→ Submission blocked, user sees error message

### ⚠️ **Warning Case - Trim without adapter specified**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "No adapter type specified, will use default (NexteraPE-PE)"
  ],
  "stage": "trim",
  "run_id": "abc123"
}
```
→ Job submits, warnings logged to console

---

## Testing

### Test Script: `test_validation.sh`

**Usage:**
```bash
# Test with current backend
./test_validation.sh http://localhost:8000

# Test with FastX backend
./test_validation.sh http://your-fastx-host:8000
```

**Output:**
```
Testing stage validation for run: 550190eb-8233-49c7-844b-48caab4dc3f3
================================================

📋 Validating stage: qc_raw
---
✅ VALID - Ready to submit

📋 Validating stage: trim
---
✅ VALID - Ready to submit

📋 Validating stage: star
---
❌ INVALID - Cannot submit

Errors:
  • No forward paired FASTQ files found in trimmed directory
  • No reference genome FASTA file (.fa or .fasta) found
```

---

## Files Modified

### Backend
- `backend/api/main.py`: 
  - Added `validate_stage()` endpoint (lines 323-443)
  - Modified `submit_stage()` to call validation (line 454)

### Frontend
- `frontend/src/api/client.ts`:
  - Added `StageValidation` interface
  - Added `validateStage()` method

- `frontend/src/components/StageControls.tsx`:
  - Enhanced `submitStage()` with validation call
  - Improved error display formatting

---

## Next Steps

1. **Test validation** - Try submitting STAR without reference files to see error message
2. **Upload reference** - If needed, upload custom FASTA/GTF to `runs/{RUN_ID}/reference/`
3. **Submit STAR** - Should now validate successfully with global reference files in `mapping_in/`

---

## Benefits

✅ **Prevents wasted SLURM allocations** - No jobs submitted that will immediately fail
✅ **Clear error messages** - Users know exactly what's missing
✅ **Flexible reference handling** - Per-run or global reference files
✅ **Better UX** - Validation happens transparently on submit
✅ **Debugging aid** - Warnings help identify potential issues

