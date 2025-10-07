# ExpressDiff Development Guide

## 🏗️ Architecture Overview

### Backend (FastAPI)
- **Framework**: FastAPI 0.68.2 + Uvicorn
- **Location**: `backend/`
- **Key Components**:
  - `api/main.py` - REST endpoints
  - `core/slurm.py` - Job management
  - `core/script_generator.py` - SLURM script generation
  - `core/config.py` - Configuration constants
  - `models.py` - Pydantic schemas

### Frontend (React)
- **Framework**: React 19 + TypeScript + Material-UI
- **Location**: `frontend/`
- **Key Components**:
  - `src/components/Dashboard.tsx` - Main dashboard
  - `src/components/FileUpload.tsx` - File management
  - `src/components/StageControls.tsx` - Pipeline execution
  - `src/api/client.ts` - Backend API client

### SLURM Integration
- **Templates**: `slurm_templates/*.slurm.template`
- **Generated Scripts**: `runs/{run_id}/scripts/`
- **Completion Flags**: `runs/{run_id}/{stage}/{stage}_done.flag`

---

## 🛠️ Development Workflow

### Setting Up Development Environment
```bash
# Backend setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup  
module load nodejs
cd frontend
npm install
```

### Running in Development Mode
```bash
# Terminal 1: Backend with auto-reload
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend with hot reload
cd frontend
export REACT_APP_API_URL=http://localhost:8000
npm start
```

### Building for Production
```bash
# Frontend build
cd frontend
npm run build

# Backend (no build needed - Python)
# Deploy with: uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

---

## 🎯 Next Development Priorities

### High Priority
1. **Results Visualization**
   - Embed MultiQC HTML reports
   - Preview count matrices
   - Download functionality for outputs

2. **Error Handling Enhancement**  
   - Surface SLURM job error logs
   - Better validation feedback
   - Retry failed stages

3. **Real-time Updates**
   - WebSocket for live status updates  
   - Push notifications for job completion
   - Live log streaming

### Medium Priority
4. **Parameter Configuration**
   - Exposed SLURM resource settings
   - Trimming parameters (adapters, quality)
   - STAR alignment options
   - featureCounts strandedness

5. **Data Management**
   - Run deletion functionality
   - Archive/export completed runs
   - Disk usage monitoring

6. **Authentication & Security**
   - User authentication
   - Run ownership/sharing
   - API rate limiting

### Future Enhancements
7. **Differential Expression**
   - Integration with DESeq2/PyDESeq2
   - Automated DE analysis
   - Interactive plots and visualizations

8. **Performance Optimization**
   - Shared STAR genome indexes
   - Parallel stage execution where safe
   - Resource usage optimization

9. **Advanced Features**
   - Workflow templates/presets  
   - Batch run submission
   - Integration with external databases

---

## Testing

### Manual checks
```bash
# Create test data (optional)
./create_test_data.sh

# Quick API sanity checks
curl http://localhost:8000/health
curl http://localhost:8000/accounts
```

### Integration Testing
1. Create new run via UI
2. Upload test FASTQ files
3. Validate sample pairing
4. Submit QC stage and monitor
5. Progress through pipeline stages

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# List accounts
curl http://localhost:8000/accounts

# Create run
curl -X POST http://localhost:8000/runs -H "Content-Type: application/json" \
   -d '{"name": "test_run", "account": "your_account"}'
```

---

## 🐛 Common Issues & Solutions

### Python 3.6 Compatibility
- **Issue**: Legacy HPC Python version
- **Solution**: Pinned dependency versions in `requirements.txt`
- **Future**: Upgrade to Python 3.8+ when available

### SLURM Job Failures  
- **Check**: SLURM error logs in `runs/{run_id}/{stage}/*.err`
- **Debug**: Verify module availability and file permissions
- **Monitor**: Use `squeue` and `sacct` commands

### Frontend Build Issues
- **Node Version**: Ensure compatible Node.js version (18+)
- **Dependencies**: Clear `node_modules` and reinstall if needed
- **CORS**: Backend allows all origins in development mode

### File Upload Problems
- **Size Limits**: Check `MAX_UPLOAD_SIZE` in config
- **Extensions**: Verify allowed file types
- **Permissions**: Ensure write access to `runs/` directory

---

## 📝 Code Style Guidelines

### Python (Backend)
- Follow PEP 8 style guide
- Use type hints where possible
- Document functions with docstrings
- Handle errors gracefully

### TypeScript (Frontend)  
- Use strict TypeScript settings
- Follow React hooks best practices  
- Implement proper error boundaries
- Use Material-UI components consistently

### SLURM Templates
- Include error handling (`set -euo pipefail`)
- Document resource requirements
- Create completion flags on success
- Log progress and errors clearly

---

## 📚 Useful Commands

### Development
```bash
# Check backend logs
tail -f backend.log

# Monitor SLURM jobs
watch squeue -u $USER

# Check disk usage
du -sh runs/*/

# Validate JSON state files
python -m json.tool runs/{run_id}/state.json
```

### Debugging
```bash
# Test SLURM script generation
python -c "from backend.core.script_generator import SLURMScriptGenerator; print(SLURMScriptGenerator('.').generate_script('qc_raw', 'test_run', 'your_account'))"

# Check API client
python -c "from frontend.src.api.client import api; print(api.health())"

# Validate sample pairing
python -c "from backend.api.main import validate_samples; print(validate_samples('test_run_id'))"
```

---

## 🔗 External Dependencies

### HPC Modules Required
- `python/3.8+` (backend)
- `nodejs/18+` (frontend)  
- `fastqc` (QC stages)
- `multiqc` (QC aggregation)
- `trimmomatic` (adapter trimming)
- `star` (genome alignment)
- `parallel` (job parallelization)

### Python Packages (requirements.txt)
- FastAPI, Uvicorn (web framework)
- Pydantic (data validation)
- Pandas, NumPy (data processing)
- Aiofiles (async file handling)

### Node Packages (package.json)
- React, React-DOM (UI framework)
- Material-UI (component library)  
- Axios (HTTP client)
- TypeScript (type safety)

---

## 📖 Documentation

- **API Documentation**: http://localhost:8000/docs (auto-generated)
- **Component Props**: Inline TypeScript interfaces  
- **SLURM Templates**: Comments in `.slurm.template` files
- **Configuration**: Docstrings in `backend/core/config.py`

For questions or contributions, see the project repository or contact the development team.