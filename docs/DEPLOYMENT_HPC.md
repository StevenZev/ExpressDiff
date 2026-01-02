# HPC Deployment & Operations

This doc focuses on the “module deployment” model: a shared read-only installation plus per-user writable work directories.

## Key Concepts

### Install directory (read-only)
Contains:
- backend code
- frontend build artifacts (`frontend/build/`)
- SLURM templates (`slurm_templates/`)

The modulefile exports this path as `EXPRESSDIFF_HOME` (`ExpressDiff/modulefile:1`).

### Work directory (writable)
Contains per-user data and runtime outputs:
- `runs/` (uploads + outputs)
- `generated_slurm/` (generated SLURM scripts)
- `mapping_in/` (optional shared references under the workdir)
- `logs/` (launcher logs and PID files)

Workdir selection and defaults are defined in `ExpressDiff/backend/core/config.py:1` and summarized in `ExpressDiff/docs/CONFIGURATION.md:1`.

## Runtime Requirements (Cluster Side)

ExpressDiff submits SLURM jobs that assume certain tools are present (modules or conda envs). See:
- `ExpressDiff/docs/TOOLS_BIOINFORMATICS.md:1`
- `ExpressDiff/slurm_templates/qc_raw.slurm.template:1`

### Modules commonly expected by templates
- `fastqc`
- `multiqc`
- `parallel`
- `trimmomatic`
- `star`
- `miniforge` (used to activate a conda env for featureCounts and PyDESeq2 stages)

If your module names differ, update the templates in `ExpressDiff/slurm_templates/`.

### Conda environments expected by templates
Two templates assume a conda env named `testenv` exists:
- `ExpressDiff/slurm_templates/featurecounts.slurm.template:1` (needs `subread` → `featureCounts`)
- `ExpressDiff/slurm_templates/deseq2.slurm.template:1` (needs `pydeseq2`)

Example (adjust to your site policy):
```bash
module load miniforge
conda create -n testenv -y -c conda-forge -c bioconda python=3.11 subread
conda activate testenv
pip install pydeseq2
```

## Launching (Module Deployment)

The main launcher is `ExpressDiff/launch_expressdiff.sh:1` and is typically invoked via the wrapper `ExpressDiff/bin/ExpressDiff:1`:
```bash
ExpressDiff run
```

### Default ports (module launcher)
The launcher binds:
- Backend: `0.0.0.0:51234` (FastAPI via Uvicorn)
- Frontend: `0.0.0.0:51235` (static site via `python -m http.server`)

See `ExpressDiff/launch_expressdiff.sh:1`.

### Logs and PIDs
The launcher writes to the workdir:
- `logs/backend.log`, `logs/backend.pid`
- `logs/frontend.log`, `logs/frontend.pid`

### Avoiding writes to the install directory
In module deployments, the install directory is typically read-only. The launcher configures runtime writable paths under the workdir, including Node/npm cache locations:
- `npm_config_cache=$EXPRESSDIFF_WORKDIR/.npm`
- `npm_config_userconfig=$EXPRESSDIFF_WORKDIR/.npmrc`

See `ExpressDiff/launch_expressdiff.sh:1`.

### Stopping services
```bash
ExpressDiff stop
```
Or kill the PIDs in `$EXPRESSDIFF_WORKDIR/logs/`.

## Frontend Build Artifact

The module launcher serves the static build from:
- `$EXPRESSDIFF_HOME/frontend/build/`

If that directory is missing, build it during installation:
```bash
cd ExpressDiff/frontend
npm install
npm run build
```

## Common Operational Issues

### Port conflicts
If `51234` or `51235` are in use, the launcher may fail to start. The remediation depends on cluster policy:
- Stop old processes in your workdir PIDs (`$EXPRESSDIFF_WORKDIR/logs/*.pid`)
- Or change ports in `ExpressDiff/launch_expressdiff.sh:1`

### “No allocations shown”
The backend calls a site-specific `allocations` command and has fallbacks (`ExpressDiff/backend/core/slurm.py:1`). If your cluster does not provide `allocations`, you may need to adjust account discovery.
