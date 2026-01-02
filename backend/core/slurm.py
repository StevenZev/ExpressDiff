"""
SLURM job management module for ExpressDiff backend.
Wraps existing SLURM scripts with submission and status tracking.
"""
import subprocess
import re
import json
import getpass
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from .script_generator import SLURMScriptGenerator
from .config import Config


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class SLURMManager:
    """Manages SLURM job submission and monitoring for ExpressDiff pipeline stages."""
    
    def __init__(self, base_dir: Path = None):
        # Work directory where runs live
        self.base_dir = base_dir or Config.BASE_DIR
        self.user = getpass.getuser()
        self.script_generator = SLURMScriptGenerator(self.base_dir)
        
        # Map stage names to SLURM script paths (absolute install paths)
        self.stage_scripts = Config.SLURM_SCRIPTS
        
        # Expected completion flags for each stage (run-specific)
        self.stage_flags = {
            "qc_raw": "qc_raw/qc_raw_done.flag",
            "trim": "trimmed/trimming_done.flag",
            "qc_trimmed": "qc_trimmed/qc_trimmed_done.flag",
            "star": "star/star_alignment_done.flag", 
            "featurecounts": "featurecounts/featurecounts_done.flag",
            "deseq2": "logs/deseq2_done.flag"
        }

    def get_valid_accounts(self) -> List[str]:
        """Get available SLURM accounts for the current user."""
        try:
            print("=== DEBUG: Running allocations command ===")
            result = subprocess.run(["allocations"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
            print(f"DEBUG: Return code: {result.returncode}")
            
            if result.returncode != 0:
                print(f"allocations command failed with return code {result.returncode}")
                stderr = result.stderr.decode('utf-8') if isinstance(result.stderr, bytes) else result.stderr
                print(f"stderr: {stderr}")
                # Try fallback method
                return self._get_accounts_fallback()
                
            stdout = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
            print(f"DEBUG: stdout length: {len(stdout)} bytes")
            print(f"DEBUG: stdout (first 500 chars): {repr(stdout[:500])}")
            
            lines = stdout.strip().splitlines()
            print(f"DEBUG: Number of lines: {len(lines)}")
            
            if len(lines) < 3:
                print(f"allocations output too short ({len(lines)} lines), trying fallback")
                for i, line in enumerate(lines):
                    print(f"  Line {i}: {repr(line)}")
                return self._get_accounts_fallback()
                
            print("DEBUG: First 3 lines:")
            for i in range(min(3, len(lines))):
                print(f"  {i}: {repr(lines[i])}")
                
            data_lines = lines[2:]  # Skip headers
            
            accounts = []
            for idx, line in enumerate(data_lines):
                line = line.strip()  # Remove leading/trailing whitespace
                
                # Skip empty lines
                if not line:
                    print(f"  Data line {idx}: (empty, skipping)")
                    continue
                    
                # Skip help text lines that start with " for more information"
                if line.startswith("for more information") or line.startswith("run:"):
                    print(f"  Data line {idx}: {repr(line)} (help text, skipping)")
                    continue
                
                parts = line.split()
                print(f"  Data line {idx}: {repr(line)} -> parts: {parts}")
                
                # Valid account lines should have at least 4 parts: Account Balance Reserved Available
                if len(parts) >= 4:
                    account_name = parts[0]
                    # Additional validation: account names shouldn't contain common help text words
                    if not any(word in account_name.lower() for word in ["more", "information", "run:", "help"]):
                        accounts.append(account_name)
                        print(f"    -> Added account: {account_name}")
                    else:
                        print(f"    -> Skipped (contains help text keywords): {account_name}")
                else:
                    print(f"    -> Skipped (only {len(parts)} parts, need 4)")
                    
            if not accounts:
                print("No accounts parsed from allocations output, trying fallback")
                return self._get_accounts_fallback()
                
            print(f"Found {len(accounts)} SLURM accounts: {accounts}")
            return accounts
        except subprocess.TimeoutExpired:
            print("allocations command timed out, trying fallback")
            return self._get_accounts_fallback()
        except Exception as e:
            print(f"Error fetching accounts: {e}")
            import traceback
            traceback.print_exc()
            return self._get_accounts_fallback()
            
    def _get_accounts_fallback(self) -> List[str]:
        """Fallback method to get SLURM accounts using sacctmgr."""
        print("=== DEBUG: Entering fallback method ===")
        try:
            import getpass
            username = getpass.getuser()
            print(f"DEBUG: Current user: {username}")
            
            # Try using sacctmgr to get user associations
            print("DEBUG: Trying sacctmgr command")
            result = subprocess.run([
                "sacctmgr", "show", "associations", f"user={username}", "-n", "-P"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            
            print(f"DEBUG: sacctmgr return code: {result.returncode}")
            
            if result.returncode == 0:
                stdout = result.stdout.decode('utf-8')
                print(f"DEBUG: sacctmgr output length: {len(stdout)} bytes")
                print(f"DEBUG: sacctmgr output (first 500 chars): {repr(stdout[:500])}")
                
                accounts = set()
                for line in stdout.strip().splitlines():
                    parts = line.split('|')
                    if len(parts) >= 2 and parts[1]:  # Account field
                        accounts.add(parts[1])
                
                account_list = sorted(list(accounts))
                if account_list:
                    print(f"Fallback found {len(account_list)} accounts: {account_list}")
                    return account_list
                else:
                    print("DEBUG: sacctmgr returned no accounts")
            else:
                stderr = result.stderr.decode('utf-8')
                print(f"DEBUG: sacctmgr failed with stderr: {stderr}")
                    
        except Exception as e:
            print(f"Fallback method failed: {e}")
            import traceback
            traceback.print_exc()
            
        # Last resort - return common account names if nothing else works
        print("Using default account list as last resort")
        return ["default", "general", "standard"]

    def submit_job(self, stage: str, account: str, run_id: str = None, 
                   adapter_type: str = "NexteraPE-PE") -> Tuple[bool, str, Optional[str]]:
        """
        Submit a SLURM job for the specified stage.
        
        Args:
            stage: Pipeline stage name (qc_raw, trim, star, etc.)
            account: SLURM account to charge
            run_id: Run identifier for tracking (required for new system)
            adapter_type: Adapter type for trimming stage
            
        Returns:
            Tuple of (success, message, job_id)
        """
        if stage not in self.stage_scripts:
            return False, f"Unknown stage: {stage}", None
        
        if not run_id:
            return False, "Run ID is required for job submission", None
            
        # Check if any pipeline job is already running for this run
        if self._any_job_running_for_run(run_id):
            return False, f"Another pipeline job is already running for run {run_id}", None
            
        try:
            # Generate run-specific script
            script_path = self.script_generator.generate_script(
                stage=stage,
                run_id=run_id,
                account=account,
                adapter_type=adapter_type
            )
            
            # Submit the generated script
            cmd = ["sbatch", str(script_path)]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result.returncode != 0:
                stderr = result.stderr.decode('utf-8') if isinstance(result.stderr, bytes) else result.stderr
                return False, f"Job submission failed: {stderr}", None
            
            # Extract job ID from sbatch output
            stdout = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
            job_id_match = re.search(r'Submitted batch job (\d+)', stdout)
            job_id = job_id_match.group(1) if job_id_match else None
            
            return True, stdout.strip(), job_id
            
        except Exception as e:
            return False, f"Job submission failed: {str(e)}", None

    def get_job_status(self, job_id: str) -> Dict[str, str]:
        """Get status of a specific job ID using squeue/sacct."""
        try:
            # First try squeue for running jobs
            result = subprocess.run(
                ["squeue", "-j", job_id, "-o", "%.18i %.9P %.25j %.8u %.2t %.10M %.6D %R"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            if result.returncode == 0 and result.stdout:
                stdout = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
                lines = stdout.strip().splitlines()
                if len(lines) > 1:  # Header + data
                    fields = lines[1].split()
                    return {
                        "job_id": fields[0],
                        "state": fields[4], 
                        "time": fields[5] if len(fields) > 5 else "Unknown"
                    }
            
            # If not in squeue, check sacct for completed jobs
            result = subprocess.run(
                ["sacct", "-j", job_id, "--format=JobID,State,ExitCode", "--noheader"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            if result.returncode == 0 and result.stdout:
                stdout = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
                lines = stdout.strip().splitlines()
                for line in lines:
                    if line.strip() and not line.strip().endswith('.batch'):
                        fields = line.split()
                        if len(fields) >= 2:
                            return {
                                "job_id": fields[0],
                                "state": fields[1],
                                "exit_code": fields[2] if len(fields) > 2 else "Unknown"
                            }
                            
        except Exception as e:
            print(f"Error checking job status: {e}")
            
        return {"job_id": job_id, "state": "UNKNOWN", "error": "Could not determine status"}

    def check_stage_completion(self, stage: str, run_id: str = None) -> bool:
        """Check if a stage has completed by looking for its flag file."""
        if stage not in self.stage_flags:
            return False
        
        if run_id:
            # Check run-specific flag within the workdir
            flag_path = Config.RUNS_DIR / run_id / self.stage_flags[stage]
        else:
            # Check global flag (backward compatibility)
            flag_path = self.base_dir / self.stage_flags[stage]
            
        return flag_path.exists()

    def _any_job_running_for_run(self, run_id: str) -> bool:
        """Check if any pipeline jobs are currently running for a specific run."""
        try:
            result = subprocess.run(
                ["squeue", "-u", self.user, "-o", "%.18i %.9P %.25j %.50u %.2t %.10M %.6D %R"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            if result.returncode == 0:
                stdout = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
                for line in stdout.splitlines():
                    if run_id in line:
                        return True
        except Exception:
            pass
            
        return False

    def _any_job_running(self) -> bool:
        """Check if any pipeline jobs are currently running."""
        job_patterns = ["BatchTrim", "STAR", "FastQC", "featureCounts"]
        
        try:
            result = subprocess.run(
                ["squeue", "-u", self.user, "-o", "%.18i %.9P %.25j %.50u %.2t %.10M %.6D %R"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            if result.returncode == 0:
                stdout = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
                for line in stdout.splitlines():
                    for pattern in job_patterns:
                        if pattern in line:
                            return True
        except Exception:
            pass
            
        return False

    def _is_job_running(self, job_name_substring: str) -> bool:
        """Check if a specific job name pattern is running."""
        try:
            result = subprocess.run(
                ["squeue", "-u", self.user, "-o", "%.18i %.9P %.25j %.50u %.2t %.10M %.6D %R"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            if result.returncode == 0:
                stdout = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
                for line in stdout.splitlines():
                    if job_name_substring in line:
                        return True
        except Exception:
            pass
            
        return False


def load_run_state(run_id: str, runs_dir: Path = None) -> Dict:
    """Load run state from JSON file."""
    if runs_dir is None:
        runs_dir = Config.RUNS_DIR
        
    state_file = runs_dir / run_id / "state.json"
    
    if not state_file.exists():
        return {
            "run_id": run_id,
            "created_at": datetime.now().isoformat(),
            "stages": {},
            "status": "created"
        }
        
    try:
        with open(state_file) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading run state: {e}")
        return {"run_id": run_id, "error": f"Could not load state: {e}"}


def save_run_state(run_id: str, state: Dict, runs_dir: Path = None) -> bool:
    """Save run state to JSON file."""
    if runs_dir is None:
        runs_dir = Config.RUNS_DIR
        
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = run_dir / "state.json"
    
    try:
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, cls=DateTimeEncoder)
        return True
    except Exception as e:
        print(f"Error saving run state: {e}")
        return False


def update_stage_status(run_id: str, stage: str, status: str, job_id: str = None, 
                       runs_dir: Path = None) -> bool:
    """Update the status of a specific stage in the run state."""
    state = load_run_state(run_id, runs_dir)
    
    if "stages" not in state:
        state["stages"] = {}
        
    if stage not in state["stages"]:
        state["stages"][stage] = {}
        
    state["stages"][stage]["status"] = status
    state["stages"][stage]["updated_at"] = datetime.now().isoformat()
    
    if job_id:
        state["stages"][stage]["job_id"] = job_id
        
    return save_run_state(run_id, state, runs_dir)