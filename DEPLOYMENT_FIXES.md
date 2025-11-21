# ExpressDiff Deployment Fixes

## Issues Addressed

### 1. Backend Port 8000 Already in Use
**Problem**: Backend fails to start because port 8000 is already occupied by another process.

**Solution**: 
- Added `check_and_free_port()` function in `launch_expressdiff.sh` that:
  - Checks if port 8000 is in use
  - Kills any previous ExpressDiff backend process (using PID from `backend.pid` file)
  - Verifies port is free before starting new backend
  - Returns error if port is still occupied by another process

### 2. Backend Module Not Found (ModuleNotFoundError)
**Problem**: Backend fails with `ModuleNotFoundError: No module named 'backend'` because uvicorn wasn't running from the correct directory.

**Solution**:
- Set `PYTHONPATH="$INSTALL_DIR:${PYTHONPATH:-}"` before starting uvicorn
- Changed to `$INSTALL_DIR` before running backend command
- This ensures Python can import the `backend` module correctly

### 3. Frontend Writing to Read-Only Module Directory
**Problem**: Frontend tries to write files (npm cache, logs) in the module installation directory which is read-only in HPC environments.

**Solution**:
- All writable paths now point to user's work directory (`$EXPRESSDIFF_WORKDIR`, `$SCRATCH/ExpressDiff`, or `$HOME/ExpressDiff`)
- Logs stored in `$WORK_DIR/logs/` instead of `$INSTALL_DIR/logs/`
- NPM cache configured to use `$WORK_DIR/.npm` and `$WORK_DIR/.npmrc`
- When running `npx serve` or `npm start`, commands execute from `$WORK_DIR` to avoid writing to install directory

### 4. Frontend Build Process
**Problem**: Frontend was running in development mode which requires write access.

**Solution**:
- Updated EasyBuild script (`expressdiff-2.3.eb`) to build frontend during installation
- Added `npm run build` step to create static production build
- Launch script now prefers serving pre-built static files over dev server
- Uses temporary npm cache during build that gets cleaned up after

## Files Modified

1. **launch_expressdiff.sh**
   - Added port conflict detection and cleanup
   - Fixed PYTHONPATH for backend module imports
   - Ensured all writable operations use work directory
   - Improved process cleanup for both backend and frontend

2. **expressdiff-2.3.eb** (new file)
   - Updated EasyBuild configuration
   - Added frontend build step
   - Configures temporary npm cache for build process
   - Creates production-ready deployment

## Testing Recommendations

1. **Clean Test**:
   ```bash
   # Unload and reload module
   module unload expressdiff
   module load expressdiff/2.3
   
   # Remove any old processes
   pkill -f uvicorn
   pkill -f "npm start"
   
   # Launch application
   ExpressDiff run
   ```

2. **Verify Logs**:
   ```bash
   # Check work directory location
   echo $EXPRESSDIFF_WORKDIR
   
   # View logs
   tail -f $EXPRESSDIFF_WORKDIR/logs/backend.log
   tail -f $EXPRESSDIFF_WORKDIR/logs/frontend.log
   ```

3. **Check Process Status**:
   ```bash
   # Check PIDs
   cat $EXPRESSDIFF_WORKDIR/logs/backend.pid
   cat $EXPRESSDIFF_WORKDIR/logs/frontend.pid
   
   # Verify processes running
   ps -p $(cat $EXPRESSDIFF_WORKDIR/logs/backend.pid)
   ps -p $(cat $EXPRESSDIFF_WORKDIR/logs/frontend.pid)
   
   # Verify ports
   ss -tln | grep :8000
   ss -tln | grep :3000
   ```

## Directory Structure

```
Module Install Directory (read-only):
  /apps/software/standard/core/expressdiff/2.3/
    ├── bin/
    │   ├── ExpressDiff (main CLI wrapper)
    │   └── expressdiff_api.sh
    ├── backend/
    ├── frontend/
    │   └── build/ (production build - created during install)
    ├── slurm_templates/
    └── launch_expressdiff.sh

User Work Directory (writable):
  $SCRATCH/ExpressDiff/ or $HOME/ExpressDiff/
    ├── logs/
    │   ├── backend.log
    │   ├── backend.pid
    │   ├── frontend.log
    │   └── frontend.pid
    ├── runs/
    ├── mapping_in/
    ├── .npm/ (npm cache)
    └── .npmrc (npm user config)
```

## Environment Variables

- `EXPRESSDIFF_HOME`: Set by modulefile, points to install directory
- `EXPRESSDIFF_WORKDIR`: User's work directory (defaults to `$SCRATCH/ExpressDiff` or `$HOME/ExpressDiff`)
- `PYTHONPATH`: Includes install directory for backend module imports
- `npm_config_cache`: Points to work directory npm cache
- `NPM_CONFIG_CACHE`: Points to work directory npm cache

## Next Steps for DevOps

1. Deploy the updated EasyBuild script (`expressdiff-2.3.eb`)
2. Rebuild the module to include frontend production build
3. Test with the commands above
4. Verify no files are written to the module installation directory

## Contact

For questions or issues: vth3bk@virginia.edu
