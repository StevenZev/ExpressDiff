# ExpressDiff Documentation Index

This directory is the canonical documentation set for the ExpressDiff repository. If you’re unsure where to start, read `ExpressDiff/README.md:1` first.

## By Role

### End Users (Run Analyses)
- `ExpressDiff/frontend/USER_GUIDE.md:1` — full UI walkthrough, file formats, stage descriptions, result interpretation
- `ExpressDiff/frontend/QUICK_REFERENCE.md:1` — quick start + troubleshooting checklist
- `ExpressDiff/docs/DEMO_DATASET.md:1` — bundled demo dataset you can run end-to-end

### HPC Admins / Maintainers (Deploy & Operate)
- `ExpressDiff/docs/DEPLOYMENT_HPC.md:1` — module deployments, read-only installs, work directories, ports, operations
- `ExpressDiff/docs/INSTALLATION.md:1` — install options (module/source) and prerequisites
- `ExpressDiff/docs/CONFIGURATION.md:1` — environment variables, storage, ports, API base URL

### Developers (Modify Code)
- `ExpressDiff/docs/ARCHITECTURE.md:1` — backend/frontend architecture + SLURM orchestration model
- `ExpressDiff/docs/TESTING.md:1` — smoke checks and test-data generators
- `ExpressDiff/frontend/README_DEV.md:1` — frontend dev workflow

## Technical Reference
- `ExpressDiff/docs/PIPELINE.md:1` — stage I/O, dependencies, flags, outputs
- `ExpressDiff/docs/TOOLS_BIOINFORMATICS.md:1` — FastQC/MultiQC/Trimmomatic/STAR/featureCounts/DE analysis
- `ExpressDiff/docs/TOOLS_IMPLEMENTATION.md:1` — FastAPI/React/SLURM integration details

## Existing Root-Level Docs (Legacy / Historical)
Older one-off docs have been consolidated into `ExpressDiff/docs/`. If you need historical notes, use git history.

Still relevant root-level docs:
- `ExpressDiff/REPOSITORY_ORGANIZATION.md:1`
