# Architecture

ExpressDiff is a web-controlled RNA-seq pipeline for HPC environments:
- **Backend**: FastAPI service that manages runs, uploads, state, and SLURM submission
- **Frontend**: React/TypeScript UI for creating runs, uploading files, launching stages, and viewing results
- **Pipeline execution**: stage-specific SLURM scripts generated from templates

## Backend

Entry point: `ExpressDiff/backend/api/main.py:1`

Responsibilities:
- Run lifecycle (create/list/delete)
- File upload routing (FASTQ/reference/metadata)
- Stage submission with dependency enforcement
- State persistence per run (JSON)
- Serving results artifacts (e.g., featureCounts and DE results)

Key modules:
- `ExpressDiff/backend/core/config.py:1` — install/work directory and defaults
- `ExpressDiff/backend/core/slurm.py:1` — `sbatch` submission + job/status helpers
- `ExpressDiff/backend/core/script_generator.py:1` — fills templates and writes run-specific scripts

## Frontend

Location: `ExpressDiff/frontend/src/`

Responsibilities:
- Run creation + account selection
- File upload UX + validation feedback
- Stage control panel (ordered pipeline execution)
- Results views for QC, featureCounts, and DE results

See `ExpressDiff/frontend/DOCUMENTATION_INDEX.md:1`.

## SLURM Orchestration Model

1. User clicks “Run” on a stage.
2. Backend generates a stage script from a template in `ExpressDiff/slurm_templates/qc_raw.slurm.template:1`.
3. Backend submits the generated script with `sbatch`.
4. Stage writes outputs under `runs/<run_id>/...` and touches a “done flag”.
5. Backend checks flags/logs to infer completion and expose results via API.

Templates are stage-specific:
- `ExpressDiff/slurm_templates/qc_raw.slurm.template:1`
- `ExpressDiff/slurm_templates/trim.slurm.template:1`
- `ExpressDiff/slurm_templates/qc_trimmed.slurm.template:1`
- `ExpressDiff/slurm_templates/star.slurm.template:1`
- `ExpressDiff/slurm_templates/featurecounts.slurm.template:1`
- `ExpressDiff/slurm_templates/deseq2.slurm.template:1`

