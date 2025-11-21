# ExpressDiff HPC Deployment Configuration - Summary

## Issues Fixed

Based on feedback from the DevOps team, I've addressed two critical issues:

### 1. ✅ Backend Port 8000 Conflict
**Problem**: "Backend error - port 8000 is already in use"

**Root Causes**:
- Previous backend processes weren't being cleaned up
- No port availability checking before starting
- `ModuleNotFoundError: No module named 'backend'` because uvicorn wasn't running from correct directory

**Solutions Implemented**:
- Added `check_and_free_port()` function that automatically kills old ExpressDiff processes
- Set `PYTHONPATH` to include install directory so Python can find backend module
- Changed working directory to `$INSTALL_DIR` before starting uvicorn
- Improved error handling and user feedback

### 2. ✅ Frontend Writing to Read-Only Module Directory
**Problem**: "Frontend is trying to write files in the module directory"

**Root Causes**:
- npm cache and config were trying to write to install directory
- Logs were being written to module directory
- Development server (`npm start`) creates temporary files

**Solutions Implemented**:
- All writable operations redirected to work directory (`$WORK_DIR`)
- Logs stored in `$WORK_DIR/logs/` not `$INSTALL_DIR/logs/`
- npm cache configured to `$WORK_DIR/.npm`
- When running npm commands, execute from work directory
- Updated EasyBuild script to create production build (eliminates need for dev server)

## Files Changed

### Modified Files:
1. **launch_expressdiff.sh** - Main launch script with fixes for both issues
2. **expressdiff-2.3.eb** - Updated EasyBuild script with frontend build step

### New Files:
3. **DEPLOYMENT_FIXES.md** - Detailed documentation for DevOps team
4. **test_deployment.sh** - Quick validation script

## Key Changes in launch_expressdiff.sh

```bash
# 1. Port conflict detection and cleanup
check_and_free_port() {
    # Checks if port is in use
    # Kills old ExpressDiff processes
    # Verifies port is free
}

# 2. PYTHONPATH fix for backend
cd "$INSTALL_DIR"
export PYTHONPATH="$INSTALL_DIR:${PYTHONPATH:-}"

# 3. All logs in work directory
LOG_DIR="$WORK_DIR/logs"  # Not $INSTALL_DIR/logs

# 4. npm cache in work directory
export npm_config_cache="$WORK_DIR/.npm"
export NPM_CONFIG_CACHE="$WORK_DIR/.npm"

# 5. Execute npm from work directory
cd "$WORK_DIR"  # Before running npx serve or npm start
```

## Key Changes in expressdiff-2.3.eb

```python
postinstallcmds = [' && '.join([
    # ... existing commands ...
    'cd frontend',
    'export npm_config_cache=$(mktemp -d)',  # Temporary cache
    'export NPM_CONFIG_CACHE=$npm_config_cache',
    'npm install',
    'npm run build',  # NEW: Build production frontend
    'rm -rf $npm_config_cache',  # Clean up
])]
```

## Directory Structure

```
READ-ONLY Install Directory:
/apps/software/standard/core/expressdiff/2.3/
├── backend/
├── frontend/
│   └── build/          # Production build (new)
├── bin/ExpressDiff     # CLI wrapper
├── launch_expressdiff.sh
└── slurm_templates/

WRITABLE Work Directory:
$SCRATCH/ExpressDiff/ or $HOME/ExpressDiff/
├── logs/               # All logs here (not in install dir)
│   ├── backend.log
│   ├── backend.pid
│   ├── frontend.log
│   └── frontend.pid
├── runs/               # User data
├── mapping_in/         # Reference data
├── .npm/               # npm cache
└── .npmrc              # npm config
```

## Environment Variables

- `EXPRESSDIFF_HOME`: Points to install directory (set by modulefile)
- `EXPRESSDIFF_WORKDIR`: User work directory for writable files
- `PYTHONPATH`: Includes install dir for backend imports
- `npm_config_cache`, `NPM_CONFIG_CACHE`: Point to work dir npm cache

## Testing Instructions

### For You (Developer):
```bash
# 1. Test the changes locally
module load expressdiff/2.3
./test_deployment.sh

# 2. If test passes, try launching
ExpressDiff run

# 3. Check logs
tail -f $HOME/ExpressDiff/logs/backend.log
tail -f $HOME/ExpressDiff/logs/frontend.log
```

### For DevOps Team:
1. Use the new `expressdiff-2.3.eb` file to rebuild the module
2. The build will now include `npm run build` to create frontend production bundle
3. Test with: `module load expressdiff/2.3 && ExpressDiff run`
4. Verify no writes to `/apps/software/standard/core/expressdiff/2.3/`
5. Verify logs appear in user's work directory

## What DevOps Team Needs to Do

1. **Use the updated EasyBuild script**: Replace the existing `.eb` file with `expressdiff-2.3.eb`
2. **Rebuild the module**: This will create the frontend production build
3. **Test the deployment**: Use the `test_deployment.sh` script
4. **Verify write locations**: Ensure all writes go to user work directories

## Verification Checklist

- [ ] Port 8000 conflicts are automatically resolved
- [ ] Backend starts without `ModuleNotFoundError`
- [ ] No files written to `/apps/software/.../expressdiff/2.3/`
- [ ] Logs appear in `$WORK_DIR/logs/`
- [ ] Frontend serves from production build
- [ ] npm cache in `$WORK_DIR/.npm/`
- [ ] Multiple users can run simultaneously

## Contact

If you encounter any issues or have questions:
- Email: vth3bk@virginia.edu
- Check logs in `$EXPRESSDIFF_WORKDIR/logs/`

## Quick Reference Commands

```bash
# Load module
module load expressdiff/2.3

# Run validation test
./test_deployment.sh

# Start application
ExpressDiff run

# Check status
cat $EXPRESSDIFF_WORKDIR/logs/backend.pid
ps -p $(cat $EXPRESSDIFF_WORKDIR/logs/backend.pid)

# View logs
tail -f $EXPRESSDIFF_WORKDIR/logs/backend.log
tail -f $EXPRESSDIFF_WORKDIR/logs/frontend.log

# Stop services
kill $(cat $EXPRESSDIFF_WORKDIR/logs/backend.pid)
kill $(cat $EXPRESSDIFF_WORKDIR/logs/frontend.pid)

# Check ports
ss -tln | grep :8000
ss -tln | grep :3000
```
