# ExpressDiff

ExpressDiff is an HPC-oriented RNA-seq pipeline with a web UI. It provides a FastAPI backend that orchestrates SLURM stages and a React/TypeScript frontend for run creation, file upload, pipeline execution, and results viewing.

## Start Here
- Documentation index: `ExpressDiff/docs/INDEX.md:1`
- End-user guide (UI): `ExpressDiff/frontend/USER_GUIDE.md:1`
- Quick reference: `ExpressDiff/frontend/QUICK_REFERENCE.md:1`
- Bundled demo dataset: `ExpressDiff/docs/DEMO_DATASET.md:1`

## Quick Start (Users)

### HPC module deployment (recommended)
```bash
salloc -A <your_account> -p standard -c 4 --mem=16G -t 02:00:00
module load expressdiff
ExpressDiff run
```

Default module-launcher ports:
- Backend: `51234`
- Frontend: `51235`

See `ExpressDiff/docs/DEPLOYMENT_HPC.md:1`.

## Quick Start (Developers)

### Run from source (local dev defaults)
```bash
cd ExpressDiff
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd ExpressDiff/frontend
npm install
REACT_APP_API_URL=http://localhost:8000 npm start
```

Default dev ports:
- Backend: `8000`
- Frontend: `3000`

See `ExpressDiff/docs/INSTALLATION.md:1`.

## Pipeline Overview

Stages (in order) are defined by SLURM templates in `ExpressDiff/slurm_templates/qc_raw.slurm.template:1` and managed by the backend:
1. QC (raw): FastQC + MultiQC
2. Trim: Trimmomatic
3. QC (trimmed): FastQC + MultiQC
4. Align: STAR
5. Count: featureCounts
6. Differential expression: “DESeq2” stage implemented via PyDESeq2

Canonical stage reference: `ExpressDiff/docs/PIPELINE.md:1`.

## Tools Used

- Bioinformatics tools: `ExpressDiff/docs/TOOLS_BIOINFORMATICS.md:1`
- Implementation tools (FastAPI/React/SLURM integration): `ExpressDiff/docs/TOOLS_IMPLEMENTATION.md:1`

## Repository Layout

See `ExpressDiff/REPOSITORY_ORGANIZATION.md:1` for a full tree; key directories:
- `ExpressDiff/backend/` — FastAPI backend
- `ExpressDiff/frontend/` — React frontend
- `ExpressDiff/slurm_templates/` — SLURM job templates
- `ExpressDiff/test_data_generators/` — scripts to generate small test/demo data

## Support

Contact: `vth3bk@virginia.edu`
