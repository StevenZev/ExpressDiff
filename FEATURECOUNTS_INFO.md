# featureCounts Stage

## Overview
featureCounts is a highly efficient general-purpose read summarization program that counts mapped reads for genomic features such as genes, exons, promoters, and gene bodies. It's part of the Subread package.

## What It Does
- Takes aligned BAM files from STAR
- Counts how many reads map to each gene
- Creates a count matrix for differential expression analysis
- Generates a summary of assignment statistics

## Input Requirements
- ✅ **BAM files**: Aligned reads from STAR stage (`*Aligned.sortedByCoord.out.bam`)
- ✅ **GTF file**: Gene annotation (same one used for STAR)

## Output Files
- **counts.txt**: Main output - gene counts matrix with columns for each sample
- **counts.txt.summary**: Assignment statistics (assigned, unassigned_ambiguity, etc.)
- **featurecounts_done.flag**: Completion marker

## Parameters Used

```bash
featureCounts \
    -a test_annotation.gtf \          # Annotation file
    -o counts.txt \                   # Output file
    -T 8 \                            # Number of threads
    -t exon \                         # Feature type to count
    -g gene_id \                      # Attribute for gene names
    -p \                              # Paired-end reads
    -s 2 \                            # Reverse stranded (standard for most RNA-seq)
    *.bam                             # Input BAM files
```

### Parameter Explanation:
- **-t exon**: Count reads overlapping exons
- **-g gene_id**: Summarize counts at gene level (not transcript)
- **-p**: Treat fragments (paired reads) as single counting unit
- **-s 2**: Reverse stranded protocol (read 2 sense, read 1 antisense)
  - Use `-s 1` for forward stranded
  - Use `-s 0` for unstranded

## Expected Runtime
- **Test data (3 samples, 1000 reads each)**: < 1 minute
- **Real data (3 samples, 20M reads each)**: ~5-10 minutes

## Software Requirements
- **Module**: miniforge
- **Conda env**: testenv
- **Package**: subread (from bioconda)

### Installation (if needed):
```bash
module load miniforge
conda create -n testenv
conda activate testenv
conda install -c bioconda subread
```

## Common Issues

### Issue 1: featureCounts not found
**Solution**: Install subread in testenv (see above)

### Issue 2: No BAM files found
**Solution**: Ensure STAR stage completed successfully first

### Issue 3: GTF file not found
**Solution**: Upload reference files or use test reference

### Issue 4: Low assignment rate
**Possible causes**:
- Wrong strandedness setting (-s parameter)
- GTF doesn't match genome assembly
- Poor alignment quality from STAR

## Interpreting the Summary File

The `counts.txt.summary` file shows:
- **Assigned**: Reads successfully assigned to genes ✅
- **Unassigned_Ambiguity**: Reads overlapping multiple genes
- **Unassigned_NoFeatures**: Reads in intergenic regions
- **Unassigned_Unmapped**: Reads that weren't mapped by STAR

**Good assignment rate**: > 60-70% of reads assigned to genes

## Next Steps
After featureCounts completes successfully:
1. **DESeq2 analysis**: Differential expression testing
2. Download `counts.txt` for custom analysis
3. Review `counts.txt.summary` to check data quality

## File Structure
```
runs/{run_id}/featurecounts/
├── counts.txt                      # Gene count matrix
├── counts.txt.summary              # Assignment statistics
├── featurecounts_done.flag         # Completion flag
└── featurecounts_{job_id}.out      # SLURM log
```

## Counts File Format
```
Geneid    Chr    Start    End    Strand    Length    sample_A.bam    sample_B.bam    sample_C.bam
gene001   chr1   1000     2000   +         1001      150             200             175
gene002   chr1   3000     4500   -         1501      75              100             80
...
```

The last N columns (where N = number of samples) contain the actual counts used for DESeq2.
