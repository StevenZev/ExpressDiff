#!/usr/bin/env python3
"""
Debug SLURM job submission to identify issues.
Creates a minimal test and examines what happens.
"""
import sys
import time
import uuid
import subprocess
from pathlib import Path

# Add the backend to the path  
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.core.script_generator import SLURMScriptGenerator
from backend.core.slurm import SLURMManager


def debug_job_submission():
    """Create and submit a simple test job to debug issues."""
    print("=== Debug SLURM Job Submission ===")
    
    test_run_id = f"debug_{str(uuid.uuid4())[:8]}"
    test_account = "cs4770_fa25"
    
    print(f"Test run ID: {test_run_id}")
    print(f"Using account: {test_account}")
    
    # Create test environment
    base_dir = Path.cwd()
    test_dir = base_dir / "runs" / test_run_id
    raw_dir = test_dir / "raw"
    qc_dir = test_dir / "qc_raw"
    
    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    qc_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy FASTQ files with real content
    fastq_content = '''@SRR_test_1
ACGTACGTACGTACGTACGTACGTACGTACGT
+
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
@SRR_test_2
TGCATGCATGCATGCATGCATGCATGCATGCA
+
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
@SRR_test_3
GGCCGGCCGGCCGGCCGGCCGGCCGGCCGGCC
+
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
'''
    
    test_files = ["sample1_1.fastq", "sample1_2.fastq"]
    for filename in test_files:
        with open(raw_dir / filename, 'w') as f:
            f.write(fastq_content)
    
    print(f"OK: Created test directory: {test_dir}")
    print(f"OK: Created test files: {test_files}")
    
    # Generate script
    generator = SLURMScriptGenerator()
    script_path = generator.generate_script(
        stage="qc_raw",
        run_id=test_run_id,
        account=test_account,
        adapter_type="NexteraPE-PE"
    )
    
    print(f"OK: Generated script: {script_path}")
    
    # Show script content
    print("\n--- Generated Script Content ---")
    with open(script_path) as f:
        content = f.read()
        print(content)
    
    # Submit job
    print("\n--- Submitting Job ---")
    slurm_manager = SLURMManager()
    
    try:
        success, message, job_id = slurm_manager.submit_job(
            stage="qc_raw",
            account=test_account,
            run_id=test_run_id,
            adapter_type="NexteraPE-PE"
        )
        
        if success and job_id:
            print(f"OK: Job submitted: {job_id}")
            print(f"Message: {message}")
            
            # Wait a bit and check status
            print("\nWaiting 30 seconds then checking status...")
            time.sleep(30)
            
            status = slurm_manager.get_job_status(job_id)
            print(f"Job status: {status}")
            
            # Check for output files
            print(f"\nLooking for output files...")
            output_pattern = f"*{job_id}*"
            output_files = list(qc_dir.glob(output_pattern))
            
            if output_files:
                print(f"Found output files: {output_files}")
                for file_path in output_files:
                    print(f"\n--- Content of {file_path.name} ---")
                    try:
                        with open(file_path) as f:
                            print(f.read())
                    except Exception as e:
                        print(f"Could not read file: {e}")
            else:
                print("No output files found yet")
                
                # Check if there are any files in the expected output directory
                all_files = list(qc_dir.iterdir())
                print(f"Files in {qc_dir}: {all_files}")
        else:
            print(f"FAIL: Job submission failed: {message}")
            
    except Exception as e:
        print(f"FAIL: Error: {e}")
    
    print(f"\nTest directory left intact for inspection: {test_dir}")
    print(f"To clean up later: rm -rf {test_dir}")
    
    return test_run_id


if __name__ == "__main__":
    debug_job_submission()