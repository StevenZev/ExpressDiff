# ExpressDiff Storage Configuration

## Directory Structure

### Code Location (Read-Only)
```
/home/vth3bk/Pipelinin/ExpressDiff/
├── backend/              # Python backend code
├── frontend/             # React frontend
├── slurm_templates/      # SLURM script templates
├── bin/                  # CLI wrappers
├── .env                  # Environment configuration
├── launch_expressdiff.sh # Backend launcher
└── start_backend.sh      # Helper script
```

### Data Storage (Scratch - Read/Write)
```
/scratch/vth3bk/ExpressDiff/
├── runs/                 # All pipeline runs
│   └── {run_id}/
│       ├── raw/          # Uploaded FASTQ files
│       ├── trimmed/      # Trimmed reads
│       ├── qc_raw/       # QC results
│       ├── star/         # Alignment results
│       └── ...
└── generated_slurm/      # Generated SLURM scripts
```

## Starting the Backend

### Method 1: Use the helper script (RECOMMENDED)
```bash
cd /home/vth3bk/Pipelinin/ExpressDiff
./start_backend.sh
```

### Method 2: Manual start
```bash
cd /home/vth3bk/Pipelinin/ExpressDiff
source .env
bash launch_expressdiff.sh > backend.log 2>&1 &
```

## Configuration

The `.env` file sets:
- `EXPRESSDIFF_HOME=/home/vth3bk/Pipelinin/ExpressDiff` (code location)
- `EXPRESSDIFF_WORKDIR=/scratch/vth3bk/ExpressDiff` (data storage)

The backend automatically uses:
- Templates from: `$EXPRESSDIFF_HOME/slurm_templates/`
- Data storage: `$EXPRESSDIFF_WORKDIR/runs/`

## Benefits of Scratch Storage

✓ More storage space than home directory
✓ Better I/O performance for large datasets
✓ Keeps home directory clean
✓ Designed for computational workloads
✓ Separates code (git repo) from data (run outputs)

## Checking Storage Usage

```bash
# See all runs
ls -lh /scratch/vth3bk/ExpressDiff/runs/

# Check a specific run
ls -lh /scratch/vth3bk/ExpressDiff/runs/{run_id}/

# Check uploaded files
ls -lh /scratch/vth3bk/ExpressDiff/runs/{run_id}/raw/

# Check trimmed output
ls -lh /scratch/vth3bk/ExpressDiff/runs/{run_id}/trimmed/
```

## Troubleshooting

### Backend not using scratch?
Make sure you started it with the `.env` sourced:
```bash
./start_backend.sh
```

### Files in wrong location?
Stop the old backend and restart with scratch config:
```bash
pkill -f "uvicorn.*expressdiff"
./start_backend.sh
```

### Check current configuration
```bash
source .env
echo "Install: $EXPRESSDIFF_HOME"
echo "Data:    $EXPRESSDIFF_WORKDIR"
```
