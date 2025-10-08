# Deployment Cleanup Guide

## Overview

This document outlines what files and directories should be kept vs. removed for a clean deployment of ExpressDiff.

**Important**: User data (uploaded files, run outputs) are now stored in the SCRATCH directory, not in the repository.

## Files to KEEP

### Core Application
- ✅ `backend/` - FastAPI application code
- ✅ `frontend/` - React frontend application
- ✅ `bin/` - CLI wrapper scripts (ExpressDiff, expressdiff_api.sh)
- ✅ `slurm_templates/` - SLURM job templates

### Configuration & Setup
- ✅ `modulefile` - Environment module definition
- ✅ `requirements.txt` - Python dependencies
- ✅ `launch_expressdiff.sh` - Main launch script
- ✅ `setup_env.sh` - Environment setup script
- ✅ `setup.sh` - Setup script
- ✅ `start_backend.sh` - Backend start script

### Documentation
- ✅ `README.md` - Main documentation
- ✅ `DEVELOPMENT.md` - Development guide
- ✅ `DEVELOPMENT_SETUP.md` - Setup guide
- ✅ `LICENSE` - License file

### Sample Data Generators (Keep for testing)
- ✅ `create_test_data.sh` - Generate test FASTQ files
- ✅ `create_test_reference.py` - Generate test genome/GTF
- ✅ `create_demo_data.py` - Generate demo data
- ✅ `create_demo_metadata.sh` - Generate demo metadata
- ✅ `create_valid_test_data.py` - Generate valid test data
- ✅ `test_data/` - Small test FASTQ files (~577KB)

### Pictures (Optional - used in legacy README sections)
- ⚠️ `pictures/` - Screenshots for documentation (can remove if legacy docs removed)

### Reference Data (Optional - large files)
- ⚠️ `mapping_in/` - Reference genome and GTF (3.5GB - users should provide their own)
  - Consider removing and documenting where users can download reference files

## Files to REMOVE

### Old Outputs (~21GB+)
- ❌ `STAR_out/` - Old STAR alignment outputs (21GB)
- ❌ `runs/` - Old run data (now in SCRATCH)
- ❌ `raw_fastqc_out/` - Old FastQC outputs
- ❌ `raw_multiqc_out/` - Old MultiQC outputs
- ❌ `qc_logs/` - Old QC logs
- ❌ `featureCounts_logs/` - Old featureCounts logs

### Generated Files (Recreated at runtime)
- ❌ `generated_slurm/` - Generated SLURM scripts
- ❌ `backend.log` - Backend log file
- ❌ `Log.out` - Old log file
- ❌ `selected_account.txt` - User selection (regenerated)
- ❌ `selected_adapter.txt` - User selection (regenerated)
- ❌ `.env` - Environment file (user-created)

### Old/Legacy Code
- ❌ `legacy/` - Old Streamlit application
- ❌ `!old_slurm_scripts/` - Old SLURM scripts
- ❌ `setup.ipynb` - Old Jupyter notebook
- ❌ `*.slurm` (root directory) - Old SLURM scripts replaced by templates:
  - `featureCounts.slurm`
  - `qc_raw.slurm`
  - `qc_trimmed.slurm`
  - `STAR.slurm`
  - `trimAdapters4.slurm`

### Test/Debug Scripts
- ❌ `test_api.py`
- ❌ `test_backend.py`
- ❌ `test_create_delete.sh`
- ❌ `test_rerun.sh`
- ❌ `test_runtime.sh`
- ❌ `test_storage_config.sh`
- ❌ `test_trimming_fix.sh`
- ❌ `test_validation.sh`
- ❌ `debug_slurm.py`
- ❌ `diagnose_accounts.sh`
- ❌ `preflight_check.sh`
- ❌ `find_runs.sh`
- ❌ `run_deseq2.py`

### Old Documentation
- ❌ `CONTACT_INFO_UPDATES.md`
- ❌ `DEMO_DATA_README.md`
- ❌ `DEMO_QUICKSTART.md`
- ❌ `DESEQ2_IMPLEMENTATION.md`
- ❌ `DESEQ2_QUICKSTART.md`
- ❌ `DESEQ2_UI_IMPLEMENTATION.md`
- ❌ `FEATURECOUNTS_INFO.md`
- ❌ `FRONTEND_STORAGE_INFO.md`
- ❌ `METADATA_BUILDER_PLAN.md`
- ❌ `METADATA_CSV_GUIDE.md`
- ❌ `RERUN_BEHAVIOR.md`
- ❌ `SCRATCH_STORAGE_READY.md`
- ❌ `STAR_IMPROVEMENTS.md`
- ❌ `STORAGE_SETUP.md`
- ❌ `TEST_DESEQ2.md`
- ❌ `TEST_REFERENCE.md`
- ❌ `TRIMMING_ARCHITECTURE.md`
- ❌ `VALIDATION_SYSTEM.md`

### Example/Old Data
- ❌ `metadata/` - Old metadata examples

## How to Clean Up

### Option 1: Use the cleanup script (Recommended)
```bash
cd /path/to/ExpressDiff
./cleanup_for_deployment.sh
```

This script will:
1. Show what will be removed
2. Ask for confirmation
3. Remove all unnecessary files
4. Display a summary

### Option 2: Manual cleanup
```bash
cd /path/to/ExpressDiff

# Remove old outputs
rm -rf STAR_out runs raw_fastqc_out raw_multiqc_out qc_logs featureCounts_logs

# Remove generated files
rm -rf generated_slurm metadata

# Remove old SLURM scripts
rm -f *.slurm

# Remove legacy code
rm -rf legacy !old_slurm_scripts setup.ipynb

# Remove test/debug scripts
rm -f test_*.py test_*.sh debug_*.py diagnose_*.sh preflight_check.sh find_runs.sh run_deseq2.py

# Remove old documentation
rm -f *_IMPLEMENTATION.md *_QUICKSTART.md *_INFO.md *_GUIDE.md *_PLAN.md *_BEHAVIOR.md *_READY.md *_SETUP.md TEST_*.md

# Remove old logs and selections
rm -f Log.out backend.log selected_*.txt .env
```

## Space Savings

Expected space savings after cleanup:
- **STAR_out**: ~21GB
- **mapping_in**: ~3.5GB (if removed - users should provide their own)
- **runs**: ~122KB
- **Other files**: ~1-2MB

**Total**: ~21GB freed (or ~24.5GB if removing mapping_in)

## Post-Cleanup Structure

After cleanup, the repository should contain:
```
ExpressDiff/
├── backend/              # FastAPI application
├── frontend/             # React application
├── bin/                  # CLI scripts
├── slurm_templates/      # Job templates
├── test_data/            # Test FASTQ files (~577KB)
├── pictures/             # Documentation images (optional)
├── README.md
├── DEVELOPMENT.md
├── DEVELOPMENT_SETUP.md
├── LICENSE
├── requirements.txt
├── modulefile
├── launch_expressdiff.sh
├── setup_env.sh
├── create_test_data.sh   # Sample data generators
├── create_test_reference.py
└── .gitignore
```

## Important Notes

1. **User Data Location**: All user uploads and run outputs are now in `$SCRATCH/ExpressDiff/`, not in the repository.

2. **Reference Files**: The `mapping_in/` directory contains large reference files (3.5GB). Consider:
   - Removing it and documenting where users can download references
   - Or keeping it if you want to provide default references

3. **Test Data**: The `test_data/` directory is small (~577KB) and useful for testing, so it's kept.

4. **Git History**: This cleanup only removes files from the working directory. They remain in git history. To completely remove them from history (optional):
   ```bash
   git filter-branch --tree-filter 'rm -rf STAR_out runs' HEAD
   ```

5. **Backend Logs**: The `backend.log` file is regenerated each time the application starts, so it's safe to remove.

6. **.gitignore**: The updated `.gitignore` file will prevent these files from being re-added to git.
