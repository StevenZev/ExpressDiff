# Installation

ExpressDiff can be used in two common ways:

1. **HPC module deployment (recommended for users)**: shared, read-only install + per-user work directory.
2. **From source (recommended for developers)**: run FastAPI + React locally (or split HPC backend + local frontend).

## Prerequisites (All Modes)

### HPC runtime (for pipeline stages)
Pipeline stages are executed via SLURM scripts generated from templates in `ExpressDiff/slurm_templates/qc_raw.slurm.template:1`. Your cluster must provide:

- **SLURM**: `sbatch`, `squeue`, `sacct`
- **Environment Modules** (typical): `module load ...`
- **Bioinformatics tools** (see `ExpressDiff/docs/TOOLS_BIOINFORMATICS.md:1`)

## Option A: HPC Module Deployment

### What you get
- Read-only install directory (code, templates, built frontend)
- Per-user writable work directory (uploads, runs, outputs, logs)

### Typical usage
```bash
# interactive allocation (example)
salloc -A <your_account> -p standard -c 4 --mem=16G -t 02:00:00

module load expressdiff
ExpressDiff run
```

### Work directory
The work directory is determined in this order:
1. `EXPRESSDIFF_WORKDIR` (if set)
2. `$SCRATCH/ExpressDiff` (if `SCRATCH` is set)
3. `$HOME/ExpressDiff`

See `ExpressDiff/docs/CONFIGURATION.md:1`.

## Option B: From Source (Developer / Local)

### Backend (FastAPI)
```bash
cd ExpressDiff
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React)
```bash
cd ExpressDiff/frontend
npm install
REACT_APP_API_URL=http://localhost:8000 npm start
```

## Split Mode: HPC Backend + Local Frontend (SSH Tunnel)
This is common when the backend must run on compute nodes (for SLURM access), but you want the UI on your laptop.

1. Start the backend on the HPC node (pick a port you can tunnel to), for example:
   ```bash
   cd ExpressDiff
   source venv/bin/activate
   uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
   ```
2. From your local machine, create a tunnel to that node/port:
   ```bash
   ssh -N -L localhost:8000:<HPC_NODE_HOSTNAME_OR_IP>:8000 <user>@<hpc_login_host>
   ```
3. Start the frontend locally and point it at the tunneled API:
   ```bash
   cd ExpressDiff/frontend
   REACT_APP_API_URL=http://localhost:8000 npm start
   ```

If you run the module launcher on HPC (which defaults to ports `51234/51235`), tunnel those instead.
