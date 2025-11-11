# ExpressDiff
Differential Analysis Pipeline for RNA-Seq Data

## Quick Start

### Using Module (Recommended)
```bash
# Get an interactive allocation
salloc -A <your_account> -p standard -c 4 --mem=16G -t 02:00:00

# Load the module
module load ExpressDiff

# Start the pipeline
ExpressDiff run
```

### Direct Clone and Launch
```bash
# Get an interactive allocation
salloc -A <your_account> -p standard -c 4 --mem=16G -t 02:00:00

# Clone and start
git clone https://github.com/StevenZev/ExpressDiff.git
cd ExpressDiff

# Launch the application
./launch_expressdiff.sh
```

### Access the Interface
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs

---

## Workflow

1. **Create Run** - Name your analysis and select SLURM account
2. **Upload Files** - Drag & drop FASTQ files (paired-end: *_1.fq.gz, *_2.fq.gz)
3. **Validate Samples** - Automatic file pairing detection
4. **Run Pipeline** - Execute stages: QC → Trim → Align → Count
5. **Monitor Progress** - Real-time status updates and job tracking
6. **View Results** - Access MultiQC reports and count matrices

---

## Features

### File Management
- Drag & drop upload with progress tracking
- Automatic FASTQ pairing detection (_1/_2 naming)
- Support for FASTQ, FASTA, GTF, and metadata files
- Real-time upload status and error handling

### Pipeline Control
- Stage management with dependency checking
- Auto-refresh job status (every 10 seconds)
- SLURM job submission and tracking
- Prevents invalid stage execution order

### User Interface
- Tabbed workflow: Files → Pipeline → Results
- Visual progress bars and stage completion badges
- Multiple run management
- SLURM account selection and resource allocation

### Monitoring
- Live SLURM job status tracking with job IDs
- Automatic stage completion detection
- Clear error messages and validation feedback
- Pipeline completion visualization

---

## Architecture

### Backend (FastAPI)
- REST API for pipeline management
- JSON-based state persistence
- SLURM integration with job monitoring
- Pydantic models for type validation
- File upload support for FASTQ, reference, and metadata files

### Key API Endpoints
- `GET /health` - Health check
- `GET /accounts` - List available SLURM accounts
- `POST /runs` - Create new pipeline run
- `GET /runs` - List all runs
- `POST /runs/{run_id}/upload` - Upload files
- `POST /runs/{run_id}/stages/{stage}` - Submit pipeline stage
- `GET /runs/{run_id}/stages/{stage}/status` - Check stage status

### Frontend (React + TypeScript)
- Modern Material-UI interface
- Real-time status updates
- File drag-and-drop functionality
- Interactive pipeline controls

---

## Development

### Directory Structure
- `backend/core/` - Core modules (SLURM integration, configuration)
- `backend/api/` - FastAPI application and routes
- `backend/models.py` - Pydantic models
- `frontend/src/` - React components and UI
- `slurm_templates/` - SLURM job script templates

### Local Development
```bash
# Load Python 3.11.4
module load gcc/11.4.0 openmpi/4.1.4 python/3.11.4

# Install dependencies
pip install -r requirements.txt

# Start backend
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start frontend
cd frontend
npm install
npm start
```

### Test Data
```bash
cd test_data_generators
./create_test_data.sh
```
Upload the generated files from `test_data/` folder in the UI.

---

## Support

For questions, issues, or support requests:
**vth3bk@virginia.edu**

