# ExpressDiff Storage Configuration - Summary

## ✅ Configuration Complete!

Your ExpressDiff is now configured to:

### 📂 Run Code From:
```
/home/vth3bk/Pipelinin/ExpressDiff/
```
- This is your git repository with all the latest fixes
- Contains backend code, templates, and scripts
- Read-only during execution

### 💾 Store Data In:
```
/scratch/vth3bk/ExpressDiff/
```
- All uploaded FASTQ files
- All pipeline outputs (trimmed, aligned, counts)
- Run state and logs
- Better performance and more storage space

---

## 🚀 Quick Start

### On FastX (or any terminal):

1. **Start the backend:**
   ```bash
   cd /home/vth3bk/Pipelinin/ExpressDiff
   ./start_backend.sh
   ```

2. **Open the UI in your browser** and create a new run

3. **Upload files** - they will automatically go to `/scratch/vth3bk/ExpressDiff/runs/{run_id}/raw/`

4. **Run pipeline stages** - outputs will be in `/scratch/vth3bk/ExpressDiff/runs/{run_id}/`

---

## 📍 File Locations

### Where to find your data:

```bash
# List all runs
ls /scratch/vth3bk/ExpressDiff/runs/

# View uploaded files for a run
ls /scratch/vth3bk/ExpressDiff/runs/{run_id}/raw/

# View trimmed outputs
ls /scratch/vth3bk/ExpressDiff/runs/{run_id}/trimmed/

# View SLURM logs
tail -f /scratch/vth3bk/ExpressDiff/runs/{run_id}/trimmed/trim_*.out
```

---

## 🔧 What Changed

### Before:
- ❌ Multiple installations (`/home/vth3bk/ExpressDiff` and `/home/vth3bk/Pipelinin/ExpressDiff`)
- ❌ Data scattered in different locations
- ❌ Old buggy code running on fastx

### After:
- ✅ Single installation at `/home/vth3bk/Pipelinin/ExpressDiff` (git repo)
- ✅ All data centralized in `/scratch/vth3bk/ExpressDiff/`
- ✅ Latest fixed code with rebuilt trimming template
- ✅ Proper directory creation before file uploads

---

## 🧹 Cleanup Old Installation (Optional)

The old installation at `/home/vth3bk/ExpressDiff` is no longer needed:

```bash
# Backup any important data first
ls -la /home/vth3bk/ExpressDiff/runs/

# Then remove (CAREFUL!)
# rm -rf /home/vth3bk/ExpressDiff
```

---

## 📊 Benefits

✓ **Scratch storage** - Faster I/O, more space  
✓ **Clean separation** - Code in git repo, data in scratch  
✓ **Latest fixes** - Rebuilt trimming template and backend  
✓ **Easy to manage** - Single source of truth  

---

## 🐛 Troubleshooting

### If backend uses wrong location:
```bash
# Stop all backends
pkill -f "uvicorn.*expressdiff"

# Start with correct config
cd /home/vth3bk/Pipelinin/ExpressDiff
./start_backend.sh
```

### Verify configuration:
```bash
cd /home/vth3bk/Pipelinin/ExpressDiff
./test_storage_config.sh
```

### Check where backend is storing data:
```bash
tail backend.log | grep -i "base_dir\|workdir\|runs"
```

---

## 📝 Next Steps

1. **Stop the old backend on fastx** (if running)
2. **Start the new backend** with `./start_backend.sh`
3. **Create a fresh run** in the UI
4. **Upload test files** from `test_data/`
5. **Run trimming** - should work now!

All your data will be in `/scratch/vth3bk/ExpressDiff/runs/` ✨
