# Implementation Tools Used

## Backend

- Language/runtime: Python (see pinned deps in `ExpressDiff/requirements.txt:1`)
- Web framework: FastAPI + Uvicorn (`ExpressDiff/requirements.txt:1`)
- Data validation: Pydantic v2 (`ExpressDiff/backend/models.py:1`)
- Data handling: Pandas + NumPy (`ExpressDiff/requirements.txt:1`)
- Upload handling: `python-multipart`, `aiofiles` (`ExpressDiff/requirements.txt:1`)

## Frontend

- Language/runtime: TypeScript + React (`ExpressDiff/frontend/package.json:1`)
- UI library: Material UI (`@mui/material`) (`ExpressDiff/frontend/package.json:1`)
- HTTP client: Axios (`ExpressDiff/frontend/package.json:1`)
- Build tooling: Create React App (`react-scripts`) (`ExpressDiff/frontend/package.json:1`)

## HPC Integration

- Scheduler: SLURM
- Submission: `sbatch` invoked by backend (`ExpressDiff/backend/core/slurm.py:1`)
- Templates: `ExpressDiff/slurm_templates/` filled by `ExpressDiff/backend/core/script_generator.py:1`
- Module deployments: modulefile sets `EXPRESSDIFF_HOME` and defaults `EXPRESSDIFF_WORKDIR` (`ExpressDiff/modulefile:1`)

