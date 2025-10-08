#!/bin/bash
# Cleanup script to remove unnecessary files before deployment
# This removes old run data, outputs, and temporary files
# Keeps: templates, scripts for generating sample data/references, and core application code

set -euo pipefail

echo "=========================================="
echo "ExpressDiff Deployment Cleanup"
echo "=========================================="
echo ""

# Function to safely remove directories/files
safe_remove() {
    local path="$1"
    local description="$2"
    
    if [ -e "$path" ]; then
        echo "Removing: $description"
        echo "  Path: $path"
        du -sh "$path" 2>/dev/null || echo "  Size: N/A"
        rm -rf "$path"
        echo "  ✓ Removed"
        echo ""
    else
        echo "Skipping: $description (not found)"
        echo "  Path: $path"
        echo ""
    fi
}

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "Current directory: $(pwd)"
echo ""
echo "This script will remove:"
echo "  - Old run outputs (STAR_out/, runs/, etc.)"
echo "  - Old SLURM scripts in root directory"
echo "  - Generated SLURM scripts"
echo "  - QC output directories"
echo "  - Legacy streamlit code"
echo "  - Test/debug scripts"
echo "  - Old documentation markdown files"
echo "  - Pictures directory (legacy docs)"
echo "  - Reference genome/GTF files (mapping_in/ - 3.5GB)"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo ""

# Remove old run outputs (21GB STAR outputs)
safe_remove "STAR_out" "Old STAR alignment outputs (21GB)"

# Remove old run data in repository (now stored in SCRATCH)
safe_remove "runs" "Old run data (now in SCRATCH)"

# Remove old QC outputs
safe_remove "raw_fastqc_out" "Old raw FastQC outputs"
safe_remove "raw_multiqc_out" "Old raw MultiQC outputs"
safe_remove "qc_logs" "Old QC log files"
safe_remove "featureCounts_logs" "Old featureCounts log files"

# Remove generated SLURM scripts (dynamically generated)
safe_remove "generated_slurm" "Generated SLURM scripts (recreated at runtime)"

# Remove old metadata directory (examples only)
safe_remove "metadata" "Old metadata directory"

# Remove old SLURM scripts from root (replaced by templates)
safe_remove "featureCounts.slurm" "Old featureCounts SLURM script"
safe_remove "qc_raw.slurm" "Old QC raw SLURM script"
safe_remove "qc_trimmed.slurm" "Old QC trimmed SLURM script"
safe_remove "STAR.slurm" "Old STAR SLURM script"
safe_remove "trimAdapters4.slurm" "Old trim adapters SLURM script"

# Remove old SLURM script directory
safe_remove "!old_slurm_scripts" "Old SLURM scripts directory"

# Remove legacy streamlit application
safe_remove "legacy" "Legacy Streamlit application"

# Remove old notebook setup
safe_remove "setup.ipynb" "Old Jupyter notebook setup"

# Remove test/debug scripts (keep create_test_data.sh and reference generators)
safe_remove "test_api.py" "API test script"
safe_remove "test_backend.py" "Backend test script"
safe_remove "test_create_delete.sh" "Create/delete test script"
safe_remove "test_rerun.sh" "Rerun test script"
safe_remove "test_runtime.sh" "Runtime test script"
safe_remove "test_storage_config.sh" "Storage config test script"
safe_remove "test_trimming_fix.sh" "Trimming fix test script"
safe_remove "test_validation.sh" "Validation test script"
safe_remove "debug_slurm.py" "SLURM debug script"
safe_remove "diagnose_accounts.sh" "Accounts diagnostic script"
safe_remove "preflight_check.sh" "Preflight check script"
safe_remove "find_runs.sh" "Find runs script"
safe_remove "run_deseq2.py" "Standalone DESeq2 script"

# Remove old documentation files (keep main README and DEVELOPMENT docs)
safe_remove "CONTACT_INFO_UPDATES.md" "Contact info updates doc"
safe_remove "DEMO_DATA_README.md" "Demo data README"
safe_remove "DEMO_QUICKSTART.md" "Demo quickstart"
safe_remove "DESEQ2_IMPLEMENTATION.md" "DESeq2 implementation doc"
safe_remove "DESEQ2_QUICKSTART.md" "DESeq2 quickstart"
safe_remove "DESEQ2_UI_IMPLEMENTATION.md" "DESeq2 UI implementation doc"
safe_remove "FEATURECOUNTS_INFO.md" "FeatureCounts info doc"
safe_remove "FRONTEND_STORAGE_INFO.md" "Frontend storage info doc"
safe_remove "METADATA_BUILDER_PLAN.md" "Metadata builder plan"
safe_remove "METADATA_CSV_GUIDE.md" "Metadata CSV guide"
safe_remove "RERUN_BEHAVIOR.md" "Rerun behavior doc"
safe_remove "SCRATCH_STORAGE_READY.md" "Scratch storage ready doc"
safe_remove "STAR_IMPROVEMENTS.md" "STAR improvements doc"
safe_remove "STORAGE_SETUP.md" "Storage setup doc"
safe_remove "TEST_DESEQ2.md" "Test DESeq2 doc"
safe_remove "TEST_REFERENCE.md" "Test reference doc"
safe_remove "TRIMMING_ARCHITECTURE.md" "Trimming architecture doc"
safe_remove "VALIDATION_SYSTEM.md" "Validation system doc"

# Remove old log files
safe_remove "Log.out" "Old log file"
safe_remove "backend.log" "Backend log file (regenerated at runtime)"

# Remove selection files (regenerated)
safe_remove "selected_account.txt" "Selected account file"
safe_remove "selected_adapter.txt" "Selected adapter file"

# Remove environment file if it exists (should be user-created)
safe_remove ".env" "Environment file"

# Remove pictures directory (legacy documentation screenshots)
safe_remove "pictures" "Pictures directory (legacy documentation screenshots)"

# Remove reference genome/GTF files (users should provide their own)
safe_remove "mapping_in" "Reference genome and GTF files (3.5GB - users provide their own)"

echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo "Kept for deployment:"
echo "  ✓ Core application code (backend/, frontend/, bin/)"
echo "  ✓ SLURM templates (slurm_templates/)"
echo "  ✓ Sample data generators (create_test_data.sh, create_test_reference.py, etc.)"
echo "  ✓ Test data directory (test_data/)"
echo "  ✓ Module file (modulefile)"
echo "  ✓ Main documentation (README.md, DEVELOPMENT*.md)"
echo "  ✓ License and requirements (LICENSE, requirements.txt)"
echo "  ✓ Launch scripts (launch_expressdiff.sh, setup_env.sh, etc.)"
echo ""
echo "Removed:"
echo "  ✗ Old outputs and runs (~25GB+ freed)"
echo "  ✗ Legacy code and old scripts"
echo "  ✗ Temporary/debug files"
echo "  ✗ Development documentation"
echo "  ✗ Pictures directory"
echo "  ✗ Reference genome/GTF files (3.5GB)"
echo ""
echo "Note: User data is now stored in SCRATCH directory, not in repository."
echo ""
