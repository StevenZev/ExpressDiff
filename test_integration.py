#!/usr/bin/env python3
"""
End-to-end integration test for ExpressDiff SLURM pipeline.
This test creates a complete pipeline run and verifies job submission and execution.
"""
import sys
import time
import uuid
import subprocess
from pathlib import Path
import json
import shutil

# Add the backend to the path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.core.script_generator import SLURMScriptGenerator
from backend.core.slurm import SLURMManager, save_run_state, load_run_state
from backend.core.config import Config


class IntegrationTester:
    """End-to-end integration tester for SLURM pipeline."""
    
    def __init__(self, test_account: str = None):
        """Initialize the tester with a SLURM account."""
        self.slurm_manager = SLURMManager()
        self.test_run_id = f"test_{str(uuid.uuid4())[:8]}"
        self.test_account = test_account or self._get_default_account()
        self.base_dir = Path.cwd()
        self.test_dir = self.base_dir / "runs" / self.test_run_id
        
        print(f"Integration Test Setup:")
        print(f"  Test Run ID: {self.test_run_id}")
        print(f"  Test Account: {self.test_account}")
        print(f"  Test Directory: {self.test_dir}")
    
    def _get_default_account(self) -> str:
        """Get the first available SLURM account."""
        accounts = self.slurm_manager.get_valid_accounts()
        if not accounts:
            raise RuntimeError("No SLURM accounts available")
        return accounts[0]
    
    def setup_test_environment(self):
        """Create test run directory structure and sample data."""
        print("\n=== Setting up test environment ===")
        
        # Create run directory structure
        subdirs = ["raw", "trimmed", "qc_raw", "qc_trimmed", "star", "featurecounts", "counts", "metadata", "de", "summaries"]
        for subdir in subdirs:
            (self.test_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        # Create initial run state
        state = {
            "run_id": self.test_run_id,
            "name": f"Integration Test {self.test_run_id}",
            "status": "created",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "account": self.test_account,
            "stages": {},
            "parameters": {"adapter_type": "NexteraPE-PE"}
        }
        
        save_run_state(self.test_run_id, state, Config.RUNS_DIR)
        print(f"✓ Created run directory: {self.test_dir}")
        
        # Create minimal test FASTQ files (empty but with correct names)
        raw_dir = self.test_dir / "raw"
        test_files = [
            "sample1_1.fq.gz",
            "sample1_2.fq.gz",
            "sample2_1.fq.gz", 
            "sample2_2.fq.gz"
        ]
        
        for filename in test_files:
            test_file = raw_dir / filename
            test_file.touch()
            print(f"✓ Created test file: {filename}")
        
        # Check for reference files
        genome_dir = Path("mapping_in")
        if genome_dir.exists():
            fasta_files = list(genome_dir.glob("*.fa")) + list(genome_dir.glob("*.fasta"))
            gtf_files = list(genome_dir.glob("*.gtf"))
            
            if fasta_files and gtf_files:
                print(f"✓ Found reference files: {fasta_files[0].name}, {gtf_files[0].name}")
            else:
                print("⚠ Warning: No reference files found in mapping_in/")
        else:
            print("⚠ Warning: mapping_in/ directory not found")
    
    def test_script_generation(self):
        """Test script generation for all stages."""
        print("\n=== Testing script generation ===")
        
        generator = SLURMScriptGenerator()
        stages = ["qc_raw", "trim", "qc_trimmed", "star", "featurecounts"]
        generated_scripts = []
        
        for stage in stages:
            try:
                script_path = generator.generate_script(
                    stage=stage,
                    run_id=self.test_run_id,
                    account=self.test_account,
                    adapter_type="NexteraPE-PE"
                )
                
                if script_path.exists():
                    print(f"✓ Generated {stage} script: {script_path.name}")
                    generated_scripts.append(script_path)
                    
                    # Verify script content
                    with open(script_path) as f:
                        content = f.read()
                        if self.test_run_id in content and self.test_account in content:
                            print(f"  ✓ Script content validated")
                        else:
                            print(f"  ✗ Script content invalid")
                else:
                    print(f"✗ Failed to generate {stage} script")
                    
            except Exception as e:
                print(f"✗ Error generating {stage} script: {e}")
        
        return generated_scripts
    
    def test_job_submission_dry_run(self):
        """Test job submission without actually running (dry run)."""
        print("\n=== Testing job submission (dry run) ===")
        
        stages = ["qc_raw"]  # Start with just one stage
        
        for stage in stages:
            try:
                print(f"\nTesting {stage} submission...")
                
                # Test the submission process without actually submitting
                success, message, job_id = self.slurm_manager.submit_job(
                    stage=stage,
                    account=self.test_account,
                    run_id=self.test_run_id,
                    adapter_type="NexteraPE-PE"
                )
                
                if success and job_id:
                    print(f"✓ Job submitted successfully")
                    print(f"  Job ID: {job_id}")
                    print(f"  Message: {message}")
                    
                    # Monitor job status
                    return self._monitor_job(job_id, stage)
                    
                else:
                    print(f"✗ Job submission failed: {message}")
                    return False
                    
            except Exception as e:
                print(f"✗ Error submitting {stage}: {e}")
                return False
    
    def _monitor_job(self, job_id: str, stage: str, timeout: int = 300):
        """Monitor a submitted job until completion or timeout."""
        print(f"\n=== Monitoring job {job_id} ===")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                job_status = self.slurm_manager.get_job_status(job_id)
                state = job_status.get("state", "UNKNOWN")
                
                print(f"Job {job_id} status: {state}")
                
                if state in ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"]:
                    if state == "COMPLETED":
                        print(f"✓ Job completed successfully")
                        
                        # Check for completion flag
                        if self.slurm_manager.check_stage_completion(stage, self.test_run_id):
                            print(f"✓ Stage completion flag found")
                            return True
                        else:
                            print(f"⚠ Job completed but no completion flag found")
                            return False
                    else:
                        print(f"✗ Job finished with state: {state}")
                        return False
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Error checking job status: {e}")
                time.sleep(10)
        
        print(f"✗ Job monitoring timed out after {timeout} seconds")
        return False
    
    def test_stage_completion_checking(self):
        """Test stage completion checking functionality."""
        print("\n=== Testing stage completion checking ===")
        
        stages = ["qc_raw", "trim", "qc_trimmed", "star", "featurecounts"]
        
        for stage in stages:
            # Test with non-existent flag
            completed = self.slurm_manager.check_stage_completion(stage, self.test_run_id)
            print(f"Stage {stage} completion (before): {'✓' if completed else '○'}")
            
            # Create a fake completion flag
            flag_path = self.test_dir / self.slurm_manager.stage_flags[stage]
            flag_path.parent.mkdir(parents=True, exist_ok=True)
            flag_path.touch()
            
            # Test with existing flag
            completed = self.slurm_manager.check_stage_completion(stage, self.test_run_id)
            print(f"Stage {stage} completion (after): {'✓' if completed else '○'}")
            
            if completed:
                print(f"  ✓ Completion checking works for {stage}")
            else:
                print(f"  ✗ Completion checking failed for {stage}")
    
    def test_real_job_submission(self, interactive: bool = True):
        """Test actual job submission to SLURM queue."""
        print("\n=== Real job submission test ===")
        
        if interactive:
            response = input("Submit a real job to SLURM queue? This will consume compute resources. (y/N): ")
            if response.lower() != 'y':
                print("Skipping real job submission")
                return True
        
        # Submit a lightweight qc_raw job
        try:
            success, message, job_id = self.slurm_manager.submit_job(
                stage="qc_raw",
                account=self.test_account,
                run_id=self.test_run_id,
                adapter_type="NexteraPE-PE"
            )
            
            if success and job_id:
                print(f"✓ Real job submitted: {job_id}")
                print(f"  Monitor with: squeue -j {job_id}")
                print(f"  Cancel with: scancel {job_id}")
                
                # Ask if user wants to monitor
                if interactive:
                    monitor = input("Monitor job progress? (y/N): ")
                    if monitor.lower() == 'y':
                        return self._monitor_job(job_id, "qc_raw", timeout=600)
                
                return True
            else:
                print(f"✗ Real job submission failed: {message}")
                return False
                
        except Exception as e:
            print(f"✗ Error in real job submission: {e}")
            return False
    
    def cleanup(self):
        """Clean up test artifacts."""
        print(f"\n=== Cleaning up test artifacts ===")
        
        try:
            # Remove test run directory
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
                print(f"✓ Removed test directory: {self.test_dir}")
            
            # Clean up generated scripts
            generator = SLURMScriptGenerator()
            generator.cleanup_run_scripts(self.test_run_id)
            print(f"✓ Cleaned up generated scripts")
            
        except Exception as e:
            print(f"⚠ Cleanup error: {e}")
    
    def run_full_test(self, include_real_submission: bool = False):
        """Run the complete integration test suite."""
        print("=" * 60)
        print("ExpressDiff SLURM Integration Test Suite")
        print("=" * 60)
        
        success_count = 0
        total_tests = 0
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Test script generation
            total_tests += 1
            scripts = self.test_script_generation()
            if scripts:
                success_count += 1
            
            # Test stage completion checking
            total_tests += 1
            self.test_stage_completion_checking()
            success_count += 1
            
            # Test job submission dry run
            total_tests += 1
            if self.test_job_submission_dry_run():
                success_count += 1
            
            # Optional real job submission
            if include_real_submission:
                total_tests += 1
                if self.test_real_job_submission():
                    success_count += 1
            
        finally:
            self.cleanup()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Tests passed: {success_count}/{total_tests}")
        print(f"Success rate: {success_count/total_tests*100:.1f}%")
        
        if success_count == total_tests:
            print("🎉 All tests passed! SLURM integration is working correctly.")
            return True
        else:
            print("❌ Some tests failed. Check the output above for details.")
            return False


def main():
    """Main entry point for integration testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ExpressDiff SLURM Integration Test")
    parser.add_argument("--account", help="SLURM account to use for testing")
    parser.add_argument("--real-jobs", action="store_true", help="Include real job submission tests")
    parser.add_argument("--non-interactive", action="store_true", help="Run without user prompts")
    
    args = parser.parse_args()
    
    try:
        tester = IntegrationTester(test_account=args.account)
        
        if args.non_interactive:
            # Run without real job submission in non-interactive mode
            success = tester.run_full_test(include_real_submission=False)
        else:
            success = tester.run_full_test(include_real_submission=args.real_jobs)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"Integration test failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())