# DESeq2 Stage Implementation Guide

## Overview

The DESeq2 stage performs differential expression analysis using **pydeseq2** (Python implementation) rather than R DESeq2. This choice was made for better integration with the Python pipeline and to avoid R/BioConductor installation complexities on the HPC.

## Why pydeseq2 Instead of R DESeq2?

### ✅ Advantages of pydeseq2:
1. **Already installed** in your miniforge testenv conda environment
2. **Pure Python** - seamless integration with ExpressDiff pipeline
3. **No R dependencies** - avoids version conflicts and module issues
4. **Faster development** - easier debugging and maintenance
5. **Same statistical methods** - implements the same DESeq2 algorithm

### ❌ Why NOT R DESeq2:
1. R + BioConductor not available as HPC modules
2. Would require creating separate R conda environment
3. Mixed Python/R pipeline more complex to maintain
4. Harder to debug and troubleshoot
5. Requires R script interfacing

## Prerequisites

### Conda Environment Setup

You already have this working! The `testenv` environment has:
```bash
module load miniforge/24.3.0-py3.11
conda activate testenv
python --version  # Python 3.11.6
conda list | grep pydeseq2  # pydeseq2 0.5.0
```

### Required Input Files

1. **featureCounts output**: `counts.txt` from the featureCounts stage
2. **Metadata file**: `metadata.csv` with required columns:
   - `sample_name`: Must match sample names in counts file
   - `condition`: Experimental conditions (e.g., "control", "treatment")

## Metadata File Format

Create a CSV file at `{RUN_DIR}/metadata/metadata.csv`:

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
- Sample names must match the BAM file names (without `_Aligned.sortedByCoord.out.bam`)
- Column names `sample_name` and `condition` are required
- You can add additional metadata columns for future analyses

## Pipeline Integration

The DESeq2 stage has been added to:

1. **Backend Models** (`backend/models.py`):
   - Added "deseq2" to `PipelineStages.stages` list

2. **Configuration** (`backend/core/config.py`):
   - Added to `SLURM_SCRIPTS` mapping
   - Added to `STAGE_FLAGS` with completion flag
   - Added to `STAGE_DEPENDENCIES`: requires featurecounts
   - Added to `DEFAULT_RESOURCES`: 4 CPUs, 16GB RAM, 1 hour

3. **Script Generator** (`backend/core/script_generator.py`):
   - Added "deseq2" template mapping
   - Added `{RUN_DIR}` placeholder support

4. **SLURM Manager** (`backend/core/slurm.py`):
   - Added completion flag tracking

## SLURM Template Features

The `deseq2.slurm.template` includes:

1. **Automatic Conda Activation**:
   - Loads miniforge module
   - Activates testenv environment
   - Verifies pydeseq2 installation

2. **Input Validation**:
   - Checks featureCounts output exists
   - Checks metadata file exists
   - Provides clear error messages

3. **Embedded Python Script**:
   - Converts featureCounts format to DESeq2 matrix
   - Runs complete DESeq2 analysis workflow
   - Generates multiple output files

4. **Output Files** (in `{RUN_DIR}/deseq2/`):
   - `counts_matrix.csv`: Processed counts matrix
   - `full_results.csv`: All genes with statistics
   - `significant_degs.csv`: Genes with padj < 0.05, |log2FC| > 1
   - `top_degs.csv`: Top 50 most significant DEGs
   - `summary.txt`: Analysis summary statistics
   - `run_deseq2.py`: Generated Python script (for reference)

## Usage

### 1. Upload Metadata

Before running DESeq2, upload your `metadata.csv` file through the UI or manually place it in:
```
/scratch/vth3bk/ExpressDiff/runs/{RUN_ID}/metadata/metadata.csv
```

### 2. Submit DESeq2 Stage

After featureCounts completes, submit the DESeq2 stage through the UI:
1. Click on your run
2. Go to "Pipeline" tab
3. Click "Run" on the "DESeq2" stage
4. Select your SLURM account
5. Submit

### 3. Monitor Job

Check status in the UI or via SLURM:
```bash
squeue -u $USER
tail -f /scratch/vth3bk/ExpressDiff/runs/{RUN_ID}/logs/deseq2_*.out
```

### 4. View Results

Results will be in: `/scratch/vth3bk/ExpressDiff/runs/{RUN_ID}/deseq2/`

## Output Interpretation

### full_results.csv
All genes with columns:
- `baseMean`: Average normalized counts
- `log2FoldChange`: Log2 fold change (treatment vs control)
- `lfcSE`: Standard error of log2FC
- `stat`: Wald statistic
- `pvalue`: P-value
- `padj`: Adjusted p-value (FDR)

### significant_degs.csv
Filtered genes where:
- `padj < 0.05` (significant after multiple testing correction)
- `|log2FoldChange| > 1` (at least 2-fold change)

### Summary Statistics
The summary.txt file includes:
- Total genes analyzed
- Number of significant DEGs
- Upregulated genes count
- Downregulated genes count

## Demo Data Expected Results

With the synthetic demo data, you should see:
- **~20 significant DEGs**: 10 upregulated, 10 downregulated
- These are the genes intentionally created with differential expression
- Assignment rate should be ~40-50% (reads align to synthetic genome)

## Troubleshooting

### "Metadata file not found"
- Upload `metadata.csv` to `{RUN_DIR}/metadata/`
- Ensure filename is exactly `metadata.csv`

### "featureCounts output not found"
- Run featureCounts stage first
- Check that `{RUN_DIR}/featurecounts/counts.txt` exists

### "Sample names don't match"
- Sample names in metadata must match BAM file names
- For `sample_A_Aligned.sortedByCoord.out.bam`, use `sample_A` in metadata

### Conda activation fails
- Ensure miniforge module is available: `module load miniforge`
- Check testenv exists: `conda env list`
- Verify pydeseq2 installed: `conda list | grep pydeseq2`

### Memory errors
- Default is 16GB RAM
- For large datasets (>100M reads), may need to increase memory in template

## Comparison: pydeseq2 vs R DESeq2

| Feature | pydeseq2 | R DESeq2 |
|---------|----------|----------|
| Algorithm | Same | Same |
| Statistical methods | Identical | Identical |
| Installation | ✅ Already done | ❌ Needs R + BioConductor |
| Integration | ✅ Native Python | ❌ Needs R interface |
| Maintenance | ✅ Easy | ❌ Complex |
| Performance | ~Same | ~Same |
| Results | Identical | Identical |

## Future Enhancements

Potential additions for the DESeq2 stage:

1. **Configurable Parameters**:
   - Allow users to set padj threshold
   - Allow users to set log2FC threshold
   - Custom design formulas for complex experiments

2. **Visualization**:
   - Volcano plots
   - MA plots
   - Heatmaps of top DEGs
   - PCA plots

3. **Advanced Analysis**:
   - Gene set enrichment analysis (GSEA)
   - GO term enrichment
   - Pathway analysis

4. **Multiple Contrasts**:
   - Support for >2 conditions
   - All pairwise comparisons
   - Custom contrast definitions

## References

- pydeseq2 documentation: https://pydeseq2.readthedocs.io/
- Original DESeq2 paper: Love, Huber & Anders (2014) Genome Biology
- pydeseq2 benchmarking: Validated against R DESeq2 results
