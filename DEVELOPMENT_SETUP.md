🎯 Final Port Configuration:
Service	Location	Port	Purpose
Backend API	HPC	8000	FastAPI server
SSH Tunnel	Local	8000	Forward to HPC:8000
Frontend API calls	Local	8000	Connect via tunnel
Frontend App	Local	3000	React dev server


# ExpressDiff Development Setup Guide

## 🏗️ **Architecture Overview**

ExpressDiff is a dual-architecture RNA-seq pipeline:
- **Backend**: FastAPI server running on HPC (Python 3.6 compatible)
- **Frontend**: React TypeScript app running locally (requires Node.js)
- **Pipeline**: SLURM-based job execution on HPC cluster

## 🔧 **HPC Backend Setup**

### **1. Environment Setup**
```bash
cd /home/vth3bk/Pipelinin/ExpressDiff

# Activate virtual environment
source venv/bin/activate

# Verify Python version
python --version  # Should be Python 3.6.8
```

### **2. Install Dependencies**
```bash
# Install compatible versions for Python 3.6
pip install fastapi==0.68.2 uvicorn==0.15.0
pip install pydantic==1.8.2
pip install pandas==1.1.5 numpy==1.19.5
pip install aiofiles==0.7.0 python-multipart==0.0.5
pip install python-dotenv==0.19.2 typing-extensions==4.1.1
```

### **3. Start Backend Server**
```bash
# Set Python path and start server
source venv/bin/activate
PYTHONPATH=/home/vth3bk/Pipelinin/ExpressDiff python backend/api/main.py
```

### **4. Verify Backend**
```bash
# Check if server is running
ps aux | grep "python backend/api/main.py"

# Test health endpoint
curl http://localhost:8000/health

# Test SLURM accounts
curl http://localhost:8000/accounts
```

**Expected Output:**
```json
{
    "status": "healthy",
    "timestamp": "2025-09-18T12:40:57.242807",
    "version": "1.0.0"
}
```

### **5. Get HPC Node Information**
```bash
# Get current node IP (needed for SSH tunnel)
hostname -i
# Example output: 10.153.1.17

# Get node hostname
hostname -f
# Example output: udc-ba38-32c0

# Verify backend is listening on all interfaces
netstat -tlnp | grep :8000
# Should show: 0.0.0.0:8000
```

## 💻 **Local Development Setup**

### **1. SSH Tunnel Setup**

**On your LOCAL machine**, create an SSH tunnel to the HPC backend:

```bash
# Replace 10.153.1.17 with your actual HPC node IP
ssh -4 -N -L localhost:8000:10.153.1.17:8000 vth3bk@login.hpc.virginia.edu
```

**Alternative tunnel commands:**
```bash
# Using hostname instead of IP
ssh -4 -N -L localhost:8000:udc-ba38-32c0:8000 vth3bk@login.hpc.virginia.edu

# Background tunnel
ssh -4 -N -f -L localhost:8000:10.153.1.17:8000 vth3bk@login.hpc.virginia.edu
```

### **2. Test SSH Tunnel**

```bash
# Test health endpoint through tunnel
curl http://localhost:8000/health

# Test API documentation
open http://localhost:8000/docs
```

### **3. Frontend Setup**

```bash
# Clone repository locally (if needed)
git clone https://github.com/StevenZev/ExpressDiff.git
cd ExpressDiff/frontend

# Install dependencies
npm install

# Start development server with correct API URL
REACT_APP_API_URL=http://localhost:8000 npm start
```

### **4. Access Application**

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000 (tunneled)
- **API Documentation**: http://localhost:8000/docs

## 🔄 **Development Workflow**

### **Daily Startup Routine**

1. **Start HPC Backend:**
```bash
cd /home/vth3bk/Pipelinin/ExpressDiff
source venv/bin/activate
PYTHONPATH=/home/vth3bk/Pipelinin/ExpressDiff python backend/api/main.py
```

2. **Get Current Node IP:**
```bash
hostname -i
# Note this IP for tunnel setup
```

3. **Set up SSH Tunnel (LOCAL machine):**
```bash
ssh -4 -N -L localhost:8000:[NODE_IP]:8000 vth3bk@login.hpc.virginia.edu
```

4. **Start Frontend (LOCAL machine):**
```bash
cd ExpressDiff/frontend
REACT_APP_API_URL=http://localhost:8000 npm start
```

### **Quick Health Check**

```bash
# On HPC: Check backend
curl http://localhost:8000/health

# On LOCAL: Check tunnel
curl http://localhost:8000/health

# Should return identical responses
```

## 🐛 **Troubleshooting**

### **Backend Issues**

**Port already in use:**
```bash
# Kill existing processes
pkill -f "python backend/api/main.py"
lsof -ti:8000 | xargs kill -9
```

**Module not found errors:**
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/home/vth3bk/Pipelinin/ExpressDiff
```

**SLURM integration issues:**
```bash
# Test SLURM commands
squeue
sacctmgr show associations user=vth3bk format=Account
```

### **SSH Tunnel Issues**

**Cannot assign requested address:**
```bash
# Use IPv4 only and different local port (if 8000 conflicts)
ssh -4 -N -L localhost:8001:10.153.1.17:8000 vth3bk@login.hpc.virginia.edu
```

**Port conflicts:**
```bash
# Check what's using the port locally
lsof -i :8000
netstat -an | grep :8000

# Kill conflicting processes
lsof -ti:8000 | xargs kill -9
```

**Connection refused:**
- Verify HPC backend is running
- Check if node IP changed: `hostname -i`
- Ensure VPN is connected (if required)

### **Frontend Issues**

**API connection errors:**
- Verify tunnel is active: `curl http://localhost:8000/health`
- Check API URL in browser console
- Ensure REACT_APP_API_URL is set correctly

**CORS errors:**
- Backend has CORS middleware enabled
- Check browser console for specific errors

## 📋 **Environment Variables**

### **HPC Backend (.env)**
```bash
# Optional: create .env file in project root
PYTHONPATH=/home/vth3bk/Pipelinin/ExpressDiff
```

### **Local Frontend**
```bash
# Set API URL for development
export REACT_APP_API_URL=http://localhost:8000

# Or create frontend/.env.local
echo "REACT_APP_API_URL=http://localhost:8000" > frontend/.env.local
```

## 🔧 **Useful Commands**

### **Process Management**
```bash
# Check running processes
ps aux | grep -E "(python|uvicorn|node)"

# Kill all related processes
pkill -f "python backend/api/main.py"
pkill -f "ssh.*-L"
pkill -f "npm start"
```

### **Network Debugging**
```bash
# Check ports on HPC
netstat -tlnp | grep -E ":(8000|3000)"

# Check SSH tunnels on local machine
ps aux | grep "ssh.*-L"
lsof -i :8000
```

### **Git Workflow**
```bash
# Keep frontend and backend in sync
git pull origin v2
git status
git add .
git commit -m "Development changes"
git push origin v2
```

## 🚀 **Next Development Steps**

1. **File Upload Implementation** - Connect frontend upload to backend
2. **Stage Execution** - Wire up Run buttons to SLURM job submission
3. **Real-time Updates** - Add polling for job status
4. **Results Visualization** - Display QC reports and DE results

## 📞 **Support**

For questions, issues, or development assistance:
- **ExpressDiff Application**: vth3bk@virginia.edu
- **HPC Issues**: Contact UVA Research Computing
- **Code Issues**: Check GitHub issues or create new ones
- **SLURM Problems**: Verify account permissions and quota

---

*Last updated: September 18, 2025*
*Compatible with: Python 3.6.8, Node.js 16+, UVA HPC*

### 3. Clone and Setup Repository

```bash
# Navigate to your work directory
cd /scratch/$USER  # or your preferred directory

# Clone the repository
git clone https://github.com/StevenZev/ExpressDiff.git
cd ExpressDiff

# Switch to development branch if needed
git checkout v2  # or your development branch
```

### 4. Environment Setup

#### Backend Setup (Python/FastAPI)
```bash
# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# If you need PyDESeq2 (requires Python 3.8+)
pip install pydeseq2
```

#### Frontend Setup (React/TypeScript)
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to project root
cd ..
```

## Application Startup

### Method 1: Full Development Setup (Recommended)

#### Start Backend (FastAPI)
```bash
# In terminal 1 - Start backend server
source venv/bin/activate
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# The backend will be available at http://COMPUTE_NODE_IP:8000
```

#### Start Frontend (React Development Server)
```bash
# In terminal 2 - Start frontend development server
cd frontend
npm start

# The frontend will be available at http://COMPUTE_NODE_IP:3000
```

### Method 2: Using Existing Streamlit Setup

If you prefer to use the existing Streamlit interface:

```bash
# Activate environment
source venv/bin/activate

# Install Streamlit if not already installed
pip install streamlit

# Start Streamlit app
python -m streamlit run expressdiff.py --server.maxUploadSize 1000000 --server.port 8501 --server.address 0.0.0.0
```

## Local Tunneling

### Method 1: SSH Tunneling (Recommended)

#### For Full Development Stack:
```bash
# On your local machine, create SSH tunnels
# Replace 'your_username' and 'udc-ba26-1c0' with your actual details

# Tunnel for backend (FastAPI)
ssh -L 8000:udc-ba26-1c0:8000 your_username@rivanna.hpc.virginia.edu

# In a separate terminal, tunnel for frontend (React)
ssh -L 3000:udc-ba26-1c0:3000 your_username@rivanna.hpc.virginia.edu
```

#### For Streamlit Only:
```bash
# Tunnel for Streamlit
ssh -L 8501:udc-ba26-1c0:8501 your_username@rivanna.hpc.virginia.edu
```

### Method 2: Multiple Tunnels in One Command
```bash
# Tunnel both ports in one command
ssh -L 8000:udc-ba26-1c0:8000 -L 3000:udc-ba26-1c0:3000 your_username@rivanna.hpc.virginia.edu
```

### Method 3: VS Code Remote Development

If using VS Code:

1. Install "Remote - SSH" extension
2. Connect to HPC via SSH
3. Open the ExpressDiff folder remotely
4. Use integrated terminal to start services
5. Forward ports through VS Code interface

## Accessing the Application

Once tunneling is established:

### Full Development Stack:
- **Frontend (React)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (FastAPI auto-generated docs)

### Streamlit Interface:
- **Streamlit App**: http://localhost:8501

## Development Workflow

### 1. Code Changes

#### Frontend Development:
```bash
# Frontend runs with hot reload, changes will appear automatically
cd frontend
npm start  # if not already running
```

#### Backend Development:
```bash
# Backend runs with --reload flag, changes will appear automatically
source venv/bin/activate
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Testing

#### Frontend Tests:
```bash
cd frontend
npm test
```

#### Backend Tests:
```bash
# Run backend tests
python -m pytest backend/tests/  # if test directory exists
```

### 3. Git Workflow
```bash
# Make changes
git add .
git commit -m "Your commit message"
git push origin your-branch
```

## Environment Variables and Configuration

### Backend Configuration
Create a `.env` file in the project root if needed:
```bash
# Example .env file
DEBUG=True
BASE_DIR=/scratch/$USER/ExpressDiff
SLURM_ACCOUNT=your_allocation_account
```

### Frontend Configuration
Update `frontend/src/api/client.ts` if backend URL needs to be changed for development:
```typescript
// For development, might need to point to localhost:8000
const BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : '/api';
```

## Port Management

### Default Ports:
- **FastAPI Backend**: 8000
- **React Frontend**: 3000
- **Streamlit**: 8501

### If Ports Are Occupied:
```bash
# Check what's using a port
netstat -tlnp | grep :8000

# Kill process if needed
kill -9 PID_NUMBER

# Or use different ports
uvicorn backend.api.main:app --host 0.0.0.0 --port 8001
```

## Troubleshooting

### Common Issues:

#### 1. Port Already in Use
```bash
# Find and kill process using the port
lsof -ti:8000 | xargs kill -9
```

#### 2. SSH Tunnel Disconnects
```bash
# Use persistent SSH connection
ssh -o ServerAliveInterval=60 -L 8000:compute-node:8000 user@hpc.edu
```

#### 3. Node/Python Version Issues
```bash
# Load specific modules on HPC
module load nodejs
module load python/3.9.6

# Or check available versions
module avail python
module avail nodejs
```

#### 4. Permission Issues
```bash
# Make sure you're in the right directory with write permissions
ls -la
chmod +x scripts/*  # if needed
```

#### 5. Compute Node Changes
When your job allocation changes to a different compute node, update your tunnels:
```bash
# Check current node
hostname

# Update SSH tunnels with new node name
ssh -L 8000:new-node-name:8000 user@hpc.edu
```

### Debug Commands:
```bash
# Check if services are running
curl http://localhost:8000/health  # Backend health check
curl http://localhost:3000         # Frontend check

# Check HPC job status
squeue -u $USER

# Check allocated resources
scontrol show job $SLURM_JOB_ID
```

## Security Notes

⚠️ **Development Only**: This setup is for development purposes only. For production:
- Use proper authentication
- Configure CORS appropriately
- Use HTTPS
- Implement proper security headers
- Use environment-specific configurations

## Additional Resources

- [UVA HPC Documentation](https://www.rc.virginia.edu/userinfo/rivanna/overview/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/)
- [SSH Tunneling Guide](https://www.ssh.com/academy/ssh/tunneling/example)

---

**Need Help?** 
- Check the main README.md for basic setup
- Review error logs in terminal outputs
- Contact: vth3bk@virginia.edu for ExpressDiff support

- Ensure all dependencies are installed
- Verify network connectivity and SSH access