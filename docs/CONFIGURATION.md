# Configuration

## Storage Layout

ExpressDiff separates:
- **Install directory (read-only)**: code, templates, built frontend (in module deployments)
- **Work directory (writable, per-user)**: uploads, run outputs, logs

Backend configuration logic is in `ExpressDiff/backend/core/config.py:1`.

### Work directory selection
In order:
1. `EXPRESSDIFF_WORKDIR`
2. `$SCRATCH/ExpressDiff` (if `SCRATCH` is set)
3. `$HOME/ExpressDiff`

### Work directory contents (typical)
- `runs/` — all run directories and outputs
- `mapping_in/` — optional shared reference data location (if used)
- `logs/` — launcher logs + PID files (module launcher)
- `generated_slurm/` — generated SLURM scripts (from templates)

## Environment Variables

- `EXPRESSDIFF_HOME`: install directory (modulefile sets this) — see `ExpressDiff/modulefile:1`
- `EXPRESSDIFF_WORKDIR`: per-user writable directory; overrides defaults
- `SCRATCH`: used to default workdir to `$SCRATCH/ExpressDiff`
- `PYTHONPATH`: the module launcher sets this so `backend` imports resolve — see `ExpressDiff/launch_expressdiff.sh:1`
- `REACT_APP_API_URL`: frontend dev-time API URL (Create React App convention)

## Ports and URLs

ExpressDiff commonly runs in one of these modes:

### Development defaults
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

### Module launcher defaults
The module launcher uses fixed ports:
- Backend: `51234`
- Frontend: `51235`

See `ExpressDiff/launch_expressdiff.sh:1`.

### Frontend API base URL
The frontend default is defined in `ExpressDiff/frontend/src/api/client.ts:1`. In development, prefer setting `REACT_APP_API_URL` rather than changing source.

