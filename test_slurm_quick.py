#!/usr/bin/env python3
"""
Quick SLURM connectivity and submission test.
Verifies basic SLURM commands work and account access is functional.
"""
import subprocess
import sys
from pathlib import Path

# Add the backend to the path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.core.slurm import SLURMManager


def test_slurm_commands():
    """Test basic SLURM command availability."""
    print("=== Testing SLURM Command Availability ===")
    
    commands = ["squeue", "sbatch", "scancel", "sacct", "allocations"]
    
    for cmd in commands:
        try:
            result = subprocess.run([cmd, "--help"], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            if result.returncode == 0:
                print(f"✓ {cmd} available")
            else:
                print(f"✗ {cmd} not working (exit code {result.returncode})")
        except FileNotFoundError:
            print(f"✗ {cmd} not found")
        except subprocess.TimeoutExpired:
            print(f"⚠ {cmd} timed out")
        except Exception as e:
            print(f"✗ {cmd} error: {e}")


def test_account_access():
    """Test SLURM account access."""
    print("\n=== Testing SLURM Account Access ===")
    
    slurm_manager = SLURMManager()
    
    try:
        accounts = slurm_manager.get_valid_accounts()
        
        if accounts:
            print(f"✓ Found {len(accounts)} accounts:")
            for account in accounts:
                print(f"  - {account}")
            return accounts[0]  # Return first account for further testing
        else:
            print("✗ No accounts found")
            return None
            
    except Exception as e:
        print(f"✗ Error fetching accounts: {e}")
        return None


def test_queue_status():
    """Test queue status checking."""
    print("\n=== Testing Queue Status ===")
    
    try:
        import getpass
        user = getpass.getuser()
        result = subprocess.run(["squeue", "-u", user, "--format=%j"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode == 0:
            output = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
            lines = output.strip().split('\n')
            job_count = len(lines) - 1  # Exclude header
            print(f"✓ Queue accessible, {job_count} jobs found")
            
            if job_count > 0:
                print("Current jobs:")
                for line in lines[1:6]:  # Show first 5 jobs
                    print(f"  {line}")
                if job_count > 5:
                    print(f"  ... and {job_count - 5} more")
        else:
            stderr = result.stderr.decode('utf-8') if isinstance(result.stderr, bytes) else result.stderr
            print(f"✗ Queue check failed: {stderr}")
            
    except Exception as e:
        print(f"✗ Queue status error: {e}")


def test_module_system():
    """Test module system availability."""
    print("\n=== Testing Module System ===")
    
    modules_to_check = ["fastqc", "multiqc", "star", "trimmomatic", "parallel"]
    
    for module in modules_to_check:
        try:
            result = subprocess.run(["module", "avail", module], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # module command often returns info in stderr
            stdout = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
            stderr = result.stderr.decode('utf-8') if isinstance(result.stderr, bytes) else result.stderr
            output = stderr + stdout
            
            if module in output.lower():
                print(f"✓ {module} module available")
            else:
                print(f"⚠ {module} module not found")
                
        except FileNotFoundError:
            print("✗ Module system not available")
            break
        except Exception as e:
            print(f"⚠ Error checking {module}: {e}")


def test_script_validation():
    """Test generated script syntax."""
    print("\n=== Testing Script Syntax ===")
    
    sys.path.insert(0, str(Path(__file__).parent / "backend"))
    from backend.core.script_generator import SLURMScriptGenerator
    
    generator = SLURMScriptGenerator()
    
    try:
        # Generate a test script
        script_path = generator.generate_script(
            stage="qc_raw",
            run_id="syntax_test",
            account="test_account",
            adapter_type="NexteraPE-PE"
        )
        
        # Check bash syntax
        result = subprocess.run(["bash", "-n", str(script_path)], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode == 0:
            print("✓ Generated script syntax is valid")
        else:
            stderr = result.stderr.decode('utf-8') if isinstance(result.stderr, bytes) else result.stderr
            print(f"✗ Script syntax error: {stderr}")
        
        # Cleanup
        script_path.unlink()
        
    except Exception as e:
        print(f"✗ Script validation error: {e}")


def main():
    """Run all quick tests."""
    print("ExpressDiff SLURM Quick Connectivity Test")
    print("=" * 50)
    
    # Run tests
    test_slurm_commands()
    account = test_account_access()
    test_queue_status()
    test_module_system()
    test_script_validation()
    
    print("\n" + "=" * 50)
    print("Quick Test Summary:")
    
    if account:
        print(f"✓ SLURM system accessible with account: {account}")
        print("✓ Ready for integration testing")
        print(f"\nTo run full integration test:")
        print(f"  python3 test_integration.py --account {account}")
    else:
        print("✗ SLURM system issues detected")
        print("Fix the above issues before proceeding")
    
    return 0 if account else 1


if __name__ == "__main__":
    exit(main())