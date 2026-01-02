# Pipeline (Stages, Inputs/Outputs)

This is the canonical stage reference. The UI provides user-level descriptions in `ExpressDiff/frontend/USER_GUIDE.md:1`.

## Stages and Dependencies

The backend enforces stage ordering (see `ExpressDiff/backend/core/config.py:1`):

1. `qc_raw` → 2. `trim` → 3. `qc_trimmed` → 4. `star` → 5. `featurecounts` → 6. `deseq2`

## Common Run Directory Layout

For a run `<run_id>`:
- `runs/<run_id>/raw/` — uploaded FASTQ
- `runs/<run_id>/reference/` — uploaded FASTA/GTF (optional if using shared references)
- `runs/<run_id>/qc_raw/` — FastQC + MultiQC outputs
- `runs/<run_id>/trimmed/` — trimmed FASTQ outputs + trimming logs
- `runs/<run_id>/qc_trimmed/` — FastQC + MultiQC outputs for trimmed reads
- `runs/<run_id>/star/` — STAR outputs (BAM + logs + index under run)
- `runs/<run_id>/featurecounts/` — counts outputs + logs
- `runs/<run_id>/metadata/metadata.csv` — metadata for DE analysis
- `runs/<run_id>/deseq2/` — DE outputs (CSV + summary)

## Stage Details

### `qc_raw` (FastQC + MultiQC)
Template: `ExpressDiff/slurm_templates/qc_raw.slurm.template:1`

Inputs:
- `runs/<run_id>/raw/*.fq.gz` / `*.fastq.gz`

Outputs:
- `runs/<run_id>/qc_raw/fastqc_out/`
- `runs/<run_id>/qc_raw/multiqc_out/`
- Done flag: `runs/<run_id>/qc_raw/qc_raw_done.flag`

### `trim` (Trimmomatic)
Template: `ExpressDiff/slurm_templates/trim.slurm.template:1`

Inputs:
- paired-end FASTQ naming convention (`*_1.*` and `*_2.*`)
- adapter type from run parameters

Outputs:
- `runs/<run_id>/trimmed/*_paired.fq.gz` (and unpaired)
- logs: `runs/<run_id>/trimmed/logs/`
- Done flag: `runs/<run_id>/trimmed/trimming_done.flag`

### `qc_trimmed` (FastQC + MultiQC)
Template: `ExpressDiff/slurm_templates/qc_trimmed.slurm.template:1`

Inputs:
- `runs/<run_id>/trimmed/*_paired.fq.gz`

Outputs:
- `runs/<run_id>/qc_trimmed/fastqc_out/`
- `runs/<run_id>/qc_trimmed/multiqc_out/`
- Done flag: `runs/<run_id>/qc_trimmed/qc_trimmed_done.flag`

### `star` (STAR aligner)
Template: `ExpressDiff/slurm_templates/star.slurm.template:1`

Inputs:
- trimmed FASTQ
- reference FASTA + GTF from either:
  - `runs/<run_id>/reference/`, or
  - shared `mapping_in/` under workdir

Outputs:
- `runs/<run_id>/star/` (BAM + logs + per-run genome index)
- Done flag: `runs/<run_id>/star/star_alignment_done.flag`

### `featurecounts` (Subread featureCounts)
Template: `ExpressDiff/slurm_templates/featurecounts.slurm.template:1`

Inputs:
- STAR BAM files under `runs/<run_id>/star/`
- GTF (run-specific or shared)

Outputs:
- `runs/<run_id>/featurecounts/counts.txt`
- `runs/<run_id>/featurecounts/counts.txt.summary`
- Done flag: `runs/<run_id>/featurecounts/featurecounts_done.flag`

### `deseq2` (Differential expression via PyDESeq2)
Template: `ExpressDiff/slurm_templates/deseq2.slurm.template:1`

Inputs:
- `runs/<run_id>/featurecounts/counts.txt`
- `runs/<run_id>/metadata/metadata.csv`

Outputs:
- `runs/<run_id>/deseq2/full_results.csv`, `top_degs.csv`, `significant_degs.csv`, `summary.txt`, etc.
- Done flag: `runs/<run_id>/logs/deseq2_done.flag`

