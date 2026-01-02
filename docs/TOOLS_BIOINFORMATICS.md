# Bioinformatics Tools Used

This project orchestrates common RNA-seq tools via SLURM job scripts. The authoritative definitions live in `ExpressDiff/slurm_templates/qc_raw.slurm.template:1`.

## QC

### FastQC
- Purpose: per-sample read quality reports (raw + trimmed)
- Used in: `ExpressDiff/slurm_templates/qc_raw.slurm.template:1`, `ExpressDiff/slurm_templates/qc_trimmed.slurm.template:1`
- Typical module: `module load fastqc`

### MultiQC
- Purpose: aggregate FastQC outputs across samples
- Used in: `ExpressDiff/slurm_templates/qc_raw.slurm.template:1`, `ExpressDiff/slurm_templates/qc_trimmed.slurm.template:1`
- Typical module: `module load multiqc`

## Trimming

### Trimmomatic
- Purpose: adapter trimming + basic quality trimming
- Used in: `ExpressDiff/slurm_templates/trim.slurm.template:1`
- Notes:
  - Template supports locating the Trimmomatic jar via `EBROOTTRIMMOMATIC`
  - Adapter file chosen by run parameter (e.g., `NexteraPE-PE`)

## Alignment

### STAR
- Purpose: splice-aware alignment to reference genome
- Used in: `ExpressDiff/slurm_templates/star.slurm.template:1`
- Notes:
  - Builds a per-run genome index under `runs/<run_id>/star/genome_index/` (as currently templated)

## Quantification

### featureCounts (Subread)
- Purpose: count reads overlapping annotated features (genes/exons)
- Used in: `ExpressDiff/slurm_templates/featurecounts.slurm.template:1`
- Installation model in template:
  - Loads `miniforge`
  - Activates a conda env named `testenv`
  - Requires `subread` to provide `featureCounts`

## Differential Expression

### “DESeq2” stage (implemented via PyDESeq2)
- Purpose: differential expression testing on the counts matrix
- Used in: `ExpressDiff/slurm_templates/deseq2.slurm.template:1`
- Implementation details:
  - Runs a generated Python script using `pydeseq2`
  - This is not the R/Bioconductor DESeq2 package; it’s the Python implementation

## Supporting Tools

### GNU parallel
- Purpose: parallelize per-file FastQC in SLURM jobs
- Used in: `ExpressDiff/slurm_templates/qc_raw.slurm.template:1`, `ExpressDiff/slurm_templates/qc_trimmed.slurm.template:1`

