# Repository Organization

This document describes the updated and organized structure of the ExpressDiff repository after cleanup and reorganization.

## 📁 Directory Structure

```
ExpressDiff/
├── docs/                      # Consolidated documentation (start here)
│   └── INDEX.md               # Documentation entry point
├── backend/                    # FastAPI backend application
│   ├── api/                    # REST API endpoints
│   ├── core/                   # Core functionality (SLURM, config)
│   ├── models.py               # Pydantic data models
│   └── __init__.py
│
├── frontend/                   # React frontend application
│   ├── public/                 # Static assets
│   ├── src/                    # React components and code
│   │   ├── components/         # React components
│   │   ├── api/                # API client
│   │   └── App.tsx             # Main app component
│   ├── package.json            # Node dependencies
│   └── tsconfig.json           # TypeScript configuration
│
├── bin/                        # Executable scripts
│   ├── ExpressDiff             # Main CLI wrapper
│   └── expressdiff_api.sh      # API-only launcher
│
├── slurm_templates/            # SLURM job templates
│   ├── qc_raw.slurm.template
│   ├── trim.slurm.template
│   ├── qc_trimmed.slurm.template
│   ├── star.slurm.template
│   ├── featurecounts.slurm.template
│   └── deseq2.slurm.template
│
├── demo_dataset/               # Bundled demo reads/reference/metadata
│   ├── Demo Reads/             # Paired-end FASTQ (control/treatment replicates)
│   ├── Demo Reference/         # Minimal FASTA + GTF
│   └── Demo Metadata/          # metadata.csv for DE stage
│
├── test_data/                  # Generated test files (small)
│   ├── sample_A_1.fq.gz
│   ├── sample_A_2.fq.gz
│   ├── test_genome.fa
│   └── test_annotation.gtf
│
├── test_data_generators/       # Scripts to generate test data
│   ├── README.md               # Documentation for generators
│   ├── create_test_data.sh     # Generate test FASTQ files
│   ├── create_test_reference.py # Generate test genome/GTF
│   ├── create_demo_data.py     # Generate demo data
│   ├── create_demo_metadata.sh # Generate demo metadata
│   └── create_valid_test_data.py # Generate validation test data
│
├── venv/                       # Python virtual environment (gitignored)
│
├── README.md                   # Main documentation
├── LICENSE                     # MIT License
│
├── modulefile                  # HPC module definition
├── requirements.txt            # Python dependencies
│
├── launch_expressdiff.sh       # Main application launcher
├── setup_env.sh                # Environment setup script
├── start_backend.sh            # Backend-only launcher
│
└── .gitignore                  # Git ignore rules
```

## 🎯 Key Directories Explained

### Application Code

**`backend/`**
- Contains the FastAPI backend application
- Handles API requests, SLURM job submission, file management
- No user data stored here (all in SCRATCH)

**`frontend/`**
- React + TypeScript frontend application
- Material-UI components
- Communicates with backend via REST API

**`bin/`**
- CLI wrapper scripts for easy deployment
- `ExpressDiff` - Main command (supports `run`, `api`, `help`)
- `expressdiff_api.sh` - Direct API launcher

### Templates and Configuration

**`slurm_templates/`**
- Template files for SLURM job scripts
- Variables substituted at runtime (e.g., {RUN_ID}, {ACCOUNT})
- Each pipeline stage has its own template

**`modulefile`**
- Environment module definition for HPC deployment
- Sets up paths and environment variables
- Enables `module load ExpressDiff`

### Test Data

**`test_data/`**
- Small generated test files (~577KB total)
- Includes FASTQ files, genome, and GTF
- Used for quick testing and validation
- **NOT for production use**

**`demo_dataset/`**
- Bundled end-to-end demo dataset (reads + reference + metadata)
- Intended for validation and training/demonstration
- Usage guide: `ExpressDiff/docs/DEMO_DATASET.md:1`

**`test_data_generators/`** ⭐ NEW
- Scripts to generate test data
- Self-contained, no external dependencies
- See `test_data_generators/README.md` for usage
- Organized separately for clarity

## 🚫 What's NOT in Repository

The following are **not** stored in the repository (configured in `.gitignore`):

### User Data (Stored in SCRATCH)
- User-uploaded FASTQ files
- Pipeline run outputs
- STAR alignment results
- QC reports
- featureCounts results
- DESeq2 results

### Generated/Temporary Files
- `generated_slurm/` - Dynamically created SLURM scripts
- `*.log` - Log files
- `backend.log` - Backend logs
- `selected_*.txt` - User selections

### Development Files
- `venv/` - Virtual environment (recreated from requirements.txt)
- `.env` - Environment variables
- `__pycache__/` - Python cache
- `node_modules/` - Node.js packages (recreated from package.json)

### Old/Removed
- `STAR_out/` - Old outputs (removed in cleanup)
- `mapping_in/` - Reference files (removed - users provide own)
- `pictures/` - Legacy screenshots (removed)
- `legacy/` - Old Streamlit app (removed)
- Test/debug scripts (removed)
- Development markdown files (removed)

## 📝 Documentation Files

**Main Documentation:**
- `README.md` - User-facing documentation and quick start
- `docs/INDEX.md` - Canonical documentation index (roles + technical references)
- `LICENSE` - MIT License

**Deployment Documentation:**
- `REPOSITORY_ORGANIZATION.md` - This file

**Component Documentation:**
- `test_data_generators/README.md` - Test data generator documentation
- `frontend/DOCUMENTATION_INDEX.md` - Frontend docs entry point

## 🔧 Setup and Launch Scripts

**`launch_expressdiff.sh`**
- Main launcher for the application
- Starts both backend and frontend
- Used by `ExpressDiff run` command

**`setup_env.sh`**
- Sets up the Python virtual environment
- Installs dependencies from requirements.txt
- Run once during initial setup

**`start_backend.sh`**
- Starts only the backend API server
- Used for API-only deployments

**`cleanup_for_deployment.sh`**
- Removes unnecessary files for deployment
- Already executed - left for documentation

## 🎯 Benefits of This Organization

### Clear Separation
- ✅ Application code separate from test utilities
- ✅ Generated data separate from code
- ✅ Documentation clearly organized
- ✅ User data stored externally (SCRATCH)

### Easy Navigation
- ✅ Test data generators in dedicated folder with README
- ✅ Templates in dedicated folder
- ✅ Frontend and backend clearly separated
- ✅ Documentation at root level

### Deployment Ready
- ✅ No unnecessary files
- ✅ Clean directory structure
- ✅ All essential files present
- ✅ Proper .gitignore configuration

### Maintainable
- ✅ Easy to find and update scripts
- ✅ Clear purpose for each directory
- ✅ Documentation co-located with code
- ✅ Logical grouping of related files

## 🚀 Quick Start for New Users

1. **Clone the repository**
   ```bash
   git clone https://github.com/StevenZev/ExpressDiff.git
   cd ExpressDiff
   ```

2. **Set up environment**
   ```bash
   ./setup_env.sh
   ```

3. **Generate test data** (optional)
   ```bash
   cd test_data_generators
   ./create_test_data.sh
   python create_test_reference.py
   ```

4. **Launch the application**
   ```bash
   ./launch_expressdiff.sh
   ```

Or using the module system:
```bash
module load ExpressDiff
ExpressDiff run
```

## 📧 Support

For questions about repository organization or deployment:
**vth3bk@virginia.edu**
