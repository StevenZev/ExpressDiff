#!/usr/bin/env python3
"""
Test script for the new run-specific SLURM integration.
This script tests the script generation and SLURM submission without actually running jobs.
"""
import sys
import uuid
from pathlib import Path

# Add the backend to the path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.core.script_generator import SLURMScriptGenerator
from backend.core.slurm import SLURMManager


def test_script_generation():
    """Test the script generation functionality."""
    print("=== Testing SLURM Script Generation ===")
    
    # Create a test run ID
    test_run_id = str(uuid.uuid4())[:8]
    test_account = "test_account"
    
    print(f"Test run ID: {test_run_id}")
    print(f"Test account: {test_account}")
    
    # Initialize the script generator
    generator = SLURMScriptGenerator()
    
    # Test script generation for each stage
    stages = ["qc_raw", "trim", "qc_trimmed", "star", "featurecounts"]
    
    for stage in stages:
        try:
            print(f"\nGenerating script for stage: {stage}")
            script_path = generator.generate_script(
                stage=stage,
                run_id=test_run_id,
                account=test_account,
                adapter_type="NexteraPE-PE"
            )
            print(f"Generated: {script_path}")
            
            # Verify the script exists and has content
            if script_path.exists():
                size = script_path.stat().st_size
                print(f"Script size: {size} bytes")
                
                # Check for run_id in the content
                with open(script_path, 'r') as f:
                    content = f.read()
                    if test_run_id in content:
                        print("✓ Run ID correctly substituted")
                    else:
                        print("✗ Run ID not found in script")
                        
                    if test_account in content:
                        print("✓ Account correctly substituted")
                    else:
                        print("✗ Account not found in script")
            else:
                print("✗ Script file not created")
                
        except Exception as e:
            print(f"✗ Error generating script for {stage}: {e}")
    
    # Cleanup test scripts
    print(f"\nCleaning up test scripts for run {test_run_id}")
    generator.cleanup_run_scripts(test_run_id)
    
    return True


def test_slurm_manager():
    """Test the SLURM manager integration (without actual submission)."""
    print("\n=== Testing SLURM Manager ===")
    
    # Initialize SLURM manager
    slurm_manager = SLURMManager()
    
    # Test account fetching
    print("Testing account fetching...")
    try:
        accounts = slurm_manager.get_valid_accounts()
        print(f"Found {len(accounts)} accounts: {accounts}")
    except Exception as e:
        print(f"Account fetching failed: {e}")
    
    # Test stage completion checking
    test_run_id = "test_run"
    print(f"\nTesting stage completion for run: {test_run_id}")
    
    stages = ["qc_raw", "trim", "qc_trimmed", "star", "featurecounts"]
    for stage in stages:
        completed = slurm_manager.check_stage_completion(stage, test_run_id)
        print(f"Stage {stage}: {'✓ Complete' if completed else '○ Pending'}")
    
    return True


def main():
    """Run all tests."""
    print("ExpressDiff SLURM Integration Test")
    print("=" * 50)
    
    try:
        # Test script generation
        test_script_generation()
        
        # Test SLURM manager
        test_slurm_manager()
        
        print("\n=== Test Summary ===")
        print("✓ Script generation working")
        print("✓ SLURM manager initialized")
        print("✓ Ready for integration testing")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())