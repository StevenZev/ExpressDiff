"""
FastAPI main application for ExpressDiff backend.
Provides REST API endpoints for RNA-seq pipeline management.
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Optional, Dict, Any
import uuid
import shutil
import json
from datetime import datetime

# Local imports
from backend.core.slurm import SLURMManager, load_run_state, save_run_state, update_stage_status
from backend.core.config import Config
from backend.models import (
    RunCreate, RunInfo, StageSubmit, JobStatus, SampleValidation, 
    HealthCheck, ErrorResponse, SuccessResponse, StageStatus, RunStatus,
    PipelineStages, FileUpload, SamplePair
)

# Initialize FastAPI app
app = FastAPI(
    title="ExpressDiff API",
    description="Backend API for RNA-seq differential expression pipeline",
    version="1.0.0"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SLURM manager
slurm_manager = SLURMManager(Config.BASE_DIR)

# Ensure directories exist
Config.RUNS_DIR.mkdir(exist_ok=True)
Config.REFERENCE_DIR.mkdir(exist_ok=True)


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(timestamp=datetime.now())


@app.get("/user")
async def get_user_info():
    """Get current user information."""
    import getpass
    import os
    
    user = getpass.getuser()
    uid = os.getuid()
    
    return {
        "username": user,
        "uid": uid,
        "computing_id": user  # Computing ID is the username
    }


@app.get("/storage-info")
async def get_storage_info():
    """Get information about data storage location."""
    import os
    import getpass
    
    base_dir = str(Config.BASE_DIR)
    install_dir = str(Config.INSTALL_DIR)
    user = getpass.getuser()
    
    # Determine storage type
    if "scratch" in base_dir.lower():
        storage_type = "scratch"
        storage_desc = "High-performance scratch storage"
    elif str(Path.home()) in base_dir:
        storage_type = "home"
        storage_desc = "Home directory storage"
    else:
        storage_type = "custom"
        storage_desc = "Custom storage location"
    
    return {
        "data_directory": base_dir,
        "install_directory": install_dir,
        "runs_directory": f"{base_dir}/runs",
        "storage_type": storage_type,
        "storage_description": storage_desc,
        "user": user,
        "persistent": True,
        "info": "All uploaded files and pipeline outputs are stored here"
    }


@app.get("/accounts", response_model=List[str])
async def get_accounts():
    """Get available SLURM accounts for the current user."""
    accounts = slurm_manager.get_valid_accounts()
    # Always return the list, even if empty or using fallback
    # The frontend will handle empty lists appropriately
    return accounts


@app.get("/stages", response_model=PipelineStages)
async def get_pipeline_stages():
    """Get available pipeline stages."""
    return PipelineStages()


@app.post("/runs", response_model=RunInfo)
async def create_run(run_request: RunCreate):
    """Create a new pipeline run."""
    run_id = str(uuid.uuid4())
    
    # Create run directory structure
    run_dir = Config.RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories for each stage (with logs)
    subdirs = [
        "raw", "trimmed", "trimmed/logs",
        "qc_raw", "qc_trimmed", 
        "star", "star/logs",
        "featurecounts", "featurecounts/logs", 
        "counts", "metadata", "de", "summaries"
    ]
    for subdir in subdirs:
        (run_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    # Initialize run state
    run_info = RunInfo(
        run_id=run_id,
        name=run_request.name,
        description=run_request.description,
        status=RunStatus.CREATED,
        created_at=datetime.now(),
        account=run_request.account,
        parameters={"adapter_type": run_request.adapter_type}
    )
    
    # Save initial state
    state = run_info.dict()
    save_run_state(run_id, state, Config.RUNS_DIR)
    
    return run_info


@app.get("/runs", response_model=List[RunInfo])
async def list_runs():
    """List all pipeline runs."""
    runs = []
    
    if not Config.RUNS_DIR.exists():
        return runs
        
    for run_dir in Config.RUNS_DIR.iterdir():
        if run_dir.is_dir():
            try:
                state = load_run_state(run_dir.name, Config.RUNS_DIR)
                if "error" not in state:
                    runs.append(RunInfo(**state))
            except Exception:
                continue  # Skip invalid run directories
                
    return sorted(runs, key=lambda x: x.created_at, reverse=True)


@app.get("/runs/{run_id}", response_model=RunInfo)
async def get_run(run_id: str):
    """Get detailed information about a specific run."""
    state = load_run_state(run_id, Config.RUNS_DIR)
    
    if "error" in state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
    return RunInfo(**state)


@app.delete("/runs/{run_id}", response_model=SuccessResponse)
async def delete_run(run_id: str):
    """Delete a pipeline run and all its associated data."""
    # Verify run exists
    state = load_run_state(run_id, Config.RUNS_DIR)
    if "error" in state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    run_dir = Config.RUNS_DIR / run_id
    
    # Check if any jobs are still running for this run
    if slurm_manager._any_job_running_for_run(run_id):
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete run while SLURM jobs are still running. Cancel jobs first."
        )
    
    try:
        # Remove the entire run directory
        shutil.rmtree(run_dir)
        
        # Also clean up any generated SLURM scripts for this run
        slurm_manager.script_generator.cleanup_run_scripts(run_id)
        
        return SuccessResponse(
            message=f"Run {run_id} deleted successfully",
            data={"run_id": run_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete run: {str(e)}")


@app.post("/runs/{run_id}/upload", response_model=SuccessResponse)
async def upload_files(run_id: str, files: List[UploadFile] = File(...)):
    """Upload FASTQ, reference, or metadata files for a run."""
    # Verify run exists
    state = load_run_state(run_id, Config.RUNS_DIR)
    if "error" in state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    run_dir = Config.RUNS_DIR / run_id
    uploaded_files = []
    
    for file in files:
        # Determine destination based on file extension
        filename_lower = file.filename.lower()
        
        if filename_lower.endswith(('.fq.gz', '.fastq.gz')):
            dest_dir = run_dir / "raw"
            dest_dir.mkdir(parents=True, exist_ok=True)
            file_type = "FASTQ"
        elif filename_lower.endswith(('.fa', '.fasta', '.gtf')):
            dest_dir = run_dir / "reference" 
            dest_dir.mkdir(parents=True, exist_ok=True)
            file_type = "Reference"
        elif filename_lower.endswith(('.csv', '.tsv')):
            dest_dir = run_dir / "metadata"
            dest_dir.mkdir(parents=True, exist_ok=True)
            file_type = "Metadata"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: .fq.gz, .fastq.gz, .fa, .fasta, .gtf, .csv, .tsv")
            
        dest_path = dest_dir / file.filename
        
        # Save file
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        uploaded_files.append({
            "filename": file.filename,
            "size": dest_path.stat().st_size,
            "type": file_type
        })
    
    return SuccessResponse(
        message=f"Uploaded {len(files)} file(s)",
        data={"files": uploaded_files}
    )


@app.get("/runs/{run_id}/samples", response_model=SampleValidation)
async def validate_samples(run_id: str):
    """Validate FASTQ sample pairing for a run."""
    # Verify run exists
    state = load_run_state(run_id, Config.RUNS_DIR)
    if "error" in state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    raw_dir = Config.RUNS_DIR / run_id / "raw"
    if not raw_dir.exists():
        return SampleValidation(total_files=0, valid_pairs=[], unpaired_files=[])
    
    # Find all FASTQ files
    fastq_files = list(raw_dir.glob("*.fq.gz")) + list(raw_dir.glob("*.fastq.gz"))
    
    # Group by sample name (assuming _1/_2 suffix pattern)
    pairs = {}
    unpaired = []
    
    for file_path in fastq_files:
        filename = file_path.name
        
        if filename.endswith("_1.fq.gz") or filename.endswith("_1.fastq.gz"):
            sample_name = filename.replace("_1.fq.gz", "").replace("_1.fastq.gz", "")
            if sample_name not in pairs:
                pairs[sample_name] = {}
            pairs[sample_name]["forward"] = filename
        elif filename.endswith("_2.fq.gz") or filename.endswith("_2.fastq.gz"):
            sample_name = filename.replace("_2.fq.gz", "").replace("_2.fastq.gz", "")
            if sample_name not in pairs:
                pairs[sample_name] = {}
            pairs[sample_name]["reverse"] = filename
        else:
            unpaired.append(filename)
    
    # Validate pairs
    valid_pairs = []
    issues = []
    
    for sample_name, files in pairs.items():
        if "forward" in files and "reverse" in files:
            valid_pairs.append(SamplePair(
                sample_name=sample_name,
                forward_file=files["forward"],
                reverse_file=files["reverse"],
                valid=True
            ))
        else:
            missing = []
            if "forward" not in files:
                missing.append("forward (_1)")
            if "reverse" not in files:
                missing.append("reverse (_2)")
            
            issues.append(f"Sample {sample_name} missing: {', '.join(missing)}")
            
            valid_pairs.append(SamplePair(
                sample_name=sample_name,
                forward_file=files.get("forward", ""),
                reverse_file=files.get("reverse", ""),
                valid=False,
                issues=missing
            ))
    
    return SampleValidation(
        total_files=len(fastq_files),
        valid_pairs=valid_pairs,
        unpaired_files=unpaired,
        issues=issues
    )


@app.get("/runs/{run_id}/stages/{stage}/validate")
async def validate_stage(run_id: str, stage: str):
    """Validate that all required files and dependencies exist for a stage."""
    # Verify run exists
    state = load_run_state(run_id, Config.RUNS_DIR)
    if "error" in state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    run_dir = Config.RUNS_DIR / run_id
    errors = []
    warnings = []
    
    # Check stage-specific requirements
    if stage == "qc_raw":
        # Check for raw FASTQ files
        raw_dir = run_dir / "raw"
        if not raw_dir.exists():
            errors.append("Raw data directory does not exist")
        else:
            fastq_files = list(raw_dir.glob("*.fq.gz")) + list(raw_dir.glob("*.fastq.gz"))
            if not fastq_files:
                errors.append("No FASTQ files found in raw directory")
            elif len(fastq_files) % 2 != 0:
                warnings.append(f"Found {len(fastq_files)} FASTQ files - expected pairs (even number)")
    
    elif stage == "trim":
        # Check for raw FASTQ files
        raw_dir = run_dir / "raw"
        if not raw_dir.exists():
            errors.append("Raw data directory does not exist")
        else:
            fastq_files = list(raw_dir.glob("*.fq.gz")) + list(raw_dir.glob("*.fastq.gz"))
            if not fastq_files:
                errors.append("No FASTQ files found in raw directory")
        
        # Check adapter type is set
        adapter_type = state.get("parameters", {}).get("adapter_type")
        if not adapter_type:
            warnings.append("No adapter type specified, will use default (NexteraPE-PE)")
    
    elif stage == "qc_trimmed":
        # Check for trimmed files
        trimmed_dir = run_dir / "trimmed"
        if not trimmed_dir.exists():
            errors.append("Trimmed data directory does not exist")
        else:
            paired_files = list(trimmed_dir.glob("*_paired.fq.gz"))
            if not paired_files:
                errors.append("No trimmed paired FASTQ files found")
    
    elif stage == "star":
        # Check for trimmed files
        trimmed_dir = run_dir / "trimmed"
        if not trimmed_dir.exists():
            errors.append("Trimmed data directory does not exist")
        else:
            forward_files = list(trimmed_dir.glob("*_forward_paired.fq.gz"))
            reverse_files = list(trimmed_dir.glob("*_reverse_paired.fq.gz"))
            if not forward_files:
                errors.append("No forward paired FASTQ files found in trimmed directory")
            if not reverse_files:
                errors.append("No reverse paired FASTQ files found in trimmed directory")
            if len(forward_files) != len(reverse_files):
                errors.append(f"Mismatch: {len(forward_files)} forward files vs {len(reverse_files)} reverse files")
        
        # Check for reference genome files
        reference_dir = run_dir / "reference"
        global_ref_dir = Config.INSTALL_DIR / "mapping_in"
        
        fasta_found = False
        gtf_found = False
        
        # Check run-specific reference first
        if reference_dir.exists():
            fasta_files = list(reference_dir.glob("*.fa")) + list(reference_dir.glob("*.fasta"))
            gtf_files = list(reference_dir.glob("*.gtf"))
            fasta_found = len(fasta_files) > 0
            gtf_found = len(gtf_files) > 0
        
        # Check global reference
        if not fasta_found or not gtf_found:
            if global_ref_dir.exists():
                if not fasta_found:
                    fasta_files = list(global_ref_dir.glob("*.fa")) + list(global_ref_dir.glob("*.fasta"))
                    fasta_found = len(fasta_files) > 0
                if not gtf_found:
                    gtf_files = list(global_ref_dir.glob("*.gtf"))
                    gtf_found = len(gtf_files) > 0
        
        if not fasta_found:
            errors.append("No reference genome FASTA file (.fa or .fasta) found in reference/ or mapping_in/")
        if not gtf_found:
            errors.append("No gene annotation GTF file (.gtf) found in reference/ or mapping_in/")
    
    elif stage == "featurecounts":
        # Check for STAR alignment output
        star_dir = run_dir / "star"
        if not star_dir.exists():
            errors.append("STAR alignment directory does not exist")
        else:
            bam_files = list(star_dir.glob("*_Aligned.sortedByCoord.out.bam"))
            if not bam_files:
                errors.append("No STAR alignment BAM files found")
        
        # Check for GTF file (same as STAR)
        reference_dir = run_dir / "reference"
        global_ref_dir = Config.INSTALL_DIR / "mapping_in"
        gtf_found = False
        
        if reference_dir.exists():
            gtf_files = list(reference_dir.glob("*.gtf"))
            gtf_found = len(gtf_files) > 0
        
        if not gtf_found and global_ref_dir.exists():
            gtf_files = list(global_ref_dir.glob("*.gtf"))
            gtf_found = len(gtf_files) > 0
        
        if not gtf_found:
            errors.append("No gene annotation GTF file (.gtf) found for feature counting")
    
    # Check dependencies
    dependencies = Config.STAGE_DEPENDENCIES.get(stage, [])
    for dep in dependencies:
        if not slurm_manager.check_stage_completion(dep, run_id):
            errors.append(f"Required stage '{dep}' has not been completed")
    
    # Return validation result
    is_valid = len(errors) == 0
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "stage": stage,
        "run_id": run_id
    }


@app.post("/runs/{run_id}/stages/{stage}", response_model=SuccessResponse)
async def submit_stage(run_id: str, stage: str, stage_request: StageSubmit):
    """Submit a pipeline stage for execution."""
    # Verify run exists
    state = load_run_state(run_id, Config.RUNS_DIR)
    if "error" in state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Verify stage is valid
    if stage not in Config.SLURM_SCRIPTS:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
    
    # Check if stage was previously completed (require confirmation to re-run)
    if slurm_manager.check_stage_completion(stage, run_id):
        if not stage_request.confirm_rerun:
            raise HTTPException(
                status_code=409,  # Conflict
                detail=f"Stage '{stage}' was previously completed. Re-running will delete previous results. Set confirm_rerun=true to proceed."
            )
    
    # Validate stage requirements (unless forced)
    if not stage_request.force:
        validation = await validate_stage(run_id, stage)
        if not validation["valid"]:
            error_msg = "Validation failed: " + "; ".join(validation["errors"])
            raise HTTPException(status_code=400, detail=error_msg)
    
    # Check dependencies unless forced
    if not stage_request.force:
        dependencies = Config.STAGE_DEPENDENCIES.get(stage, [])
        for dep in dependencies:
            if not slurm_manager.check_stage_completion(dep, run_id):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Dependency {dep} not completed. Use force=true to override."
                )
    
    # Get adapter type from run parameters
    adapter_type = state.get("parameters", {}).get("adapter_type", "NexteraPE-PE")
    
    # Submit job
    success, message, job_id = slurm_manager.submit_job(
        stage=stage, 
        account=stage_request.account, 
        run_id=run_id,
        adapter_type=adapter_type
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=message)
    
    # Update stage status
    update_stage_status(run_id, stage, StageStatus.RUNNING, job_id, Config.RUNS_DIR)
    
    return SuccessResponse(
        message=f"Stage {stage} submitted successfully",
        data={"job_id": job_id, "message": message}
    )


@app.get("/runs/{run_id}/stages/{stage}/status", response_model=JobStatus)
async def get_stage_status(run_id: str, stage: str):
    """Get the status of a specific stage."""
    # Verify run exists
    state = load_run_state(run_id, Config.RUNS_DIR)
    if "error" in state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Check if stage has been submitted
    stage_info = state.get("stages", {}).get(stage, {})
    job_id = stage_info.get("job_id")
    
    if not job_id:
        # Check for completion flag
        if slurm_manager.check_stage_completion(stage, run_id):
            return JobStatus(job_id="", state="COMPLETED")
        else:
            return JobStatus(job_id="", state="PENDING")
    
    # Check for completion flag FIRST (more reliable than SLURM exit codes)
    if slurm_manager.check_stage_completion(stage, run_id):
        update_stage_status(run_id, stage, StageStatus.COMPLETED, job_id, Config.RUNS_DIR)
        return JobStatus(job_id=job_id, state="COMPLETED")
    
    # Get job status from SLURM
    job_status = slurm_manager.get_job_status(job_id)
    
    # Update stage status if completed
    slurm_state = job_status.get("state", "UNKNOWN")
    if slurm_state in ["COMPLETED", "FAILED", "CANCELLED"]:
        new_status = StageStatus.COMPLETED if slurm_state == "COMPLETED" else StageStatus.FAILED
        update_stage_status(run_id, stage, new_status, job_id, Config.RUNS_DIR)
    
    return JobStatus(**job_status)


@app.get("/runs/{run_id}/stages/{stage}/logs")
async def get_stage_logs(run_id: str, stage: str):
    """Get the SLURM output and error logs for a specific stage."""
    import glob
    
    # Verify run exists
    state = load_run_state(run_id, Config.RUNS_DIR)
    if "error" in state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Get job ID for this stage
    stage_info = state.get("stages", {}).get(stage, {})
    job_id = stage_info.get("job_id")
    
    if not job_id:
        raise HTTPException(status_code=404, detail=f"No job ID found for stage {stage}")
    
    # Search for log files in the run directory
    # Files can be in various locations like runs/{run_id}/{stage}/ or runs/{run_id}/logs/
    run_dir = Config.RUNS_DIR / run_id
    
    # Search patterns for log files
    out_patterns = [
        str(run_dir / f"**/*{job_id}.out"),
        str(run_dir / f"*/{stage}_{job_id}.out"),
        str(run_dir / f"logs/{stage}_{job_id}.out"),
    ]
    err_patterns = [
        str(run_dir / f"**/*{job_id}.err"),
        str(run_dir / f"*/{stage}_{job_id}.err"),
        str(run_dir / f"logs/{stage}_{job_id}.err"),
    ]
    
    out_file = None
    err_file = None
    
    # Find stdout file
    for pattern in out_patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            out_file = Path(matches[0])
            break
    
    # Find stderr file  
    for pattern in err_patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            err_file = Path(matches[0])
            break
    
    result = {
        "stage": stage,
        "job_id": job_id,
        "stdout": None,
        "stderr": None,
        "stdout_file": str(out_file) if out_file else None,
        "stderr_file": str(err_file) if err_file else None
    }
    
    # Read stdout if exists
    if out_file and out_file.exists():
        try:
            with open(out_file, 'r') as f:
                result["stdout"] = f.read()
        except Exception as e:
            result["stdout"] = f"Error reading stdout: {str(e)}"
    else:
        result["stdout"] = f"Log file not found for job {job_id}. The job may still be pending, or logs may be in an unexpected location."
    
    # Read stderr if exists
    if err_file and err_file.exists():
        try:
            with open(err_file, 'r') as f:
                result["stderr"] = f.read()
        except Exception as e:
            result["stderr"] = f"Error reading stderr: {str(e)}"
    else:
        result["stderr"] = f"Error log not found for job {job_id}."
    
    return result


@app.get("/runs/{run_id}/qc/list")
async def list_qc_results(run_id: str):
    """List available QC results for a run."""
    # Verify run exists
    state = load_run_state(run_id, Config.RUNS_DIR)
    if "error" in state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    run_dir = Config.RUNS_DIR / run_id
    qc_results = {}
    
    # Check qc_raw results
    qc_raw_dir = run_dir / "qc_raw"
    if qc_raw_dir.exists():
        multiqc_html = qc_raw_dir / "multiqc_out" / "multiqc_report.html"
        fastqc_dir = qc_raw_dir / "fastqc_out"
        done_flag = qc_raw_dir / "qc_raw_done.flag"
        
        qc_results["qc_raw"] = {
            "completed": done_flag.exists(),
            "multiqc_available": multiqc_html.exists(),
            "fastqc_available": fastqc_dir.exists() and any(fastqc_dir.glob("*.html")),
            "files": []
        }
        
        # List available files
        if multiqc_html.exists():
            qc_results["qc_raw"]["files"].append({
                "name": "MultiQC Report",
                "path": "multiqc_out/multiqc_report.html",
                "type": "html",
                "description": "Aggregated quality control report"
            })
        
        # Check for additional MultiQC reports
        multiqc_dir = qc_raw_dir / "multiqc_out"
        if multiqc_dir.exists():
            for multiqc_file in multiqc_dir.glob("multiqc_report*.html"):
                if multiqc_file.name != "multiqc_report.html":  # Skip the main one we already added
                    qc_results["qc_raw"]["files"].append({
                        "name": f"MultiQC Report ({multiqc_file.stem})",
                        "path": f"multiqc_out/{multiqc_file.name}",
                        "type": "html",
                        "description": f"Additional MultiQC report: {multiqc_file.name}"
                    })
        
        if fastqc_dir.exists():
            for html_file in fastqc_dir.glob("*.html"):
                qc_results["qc_raw"]["files"].append({
                    "name": f"FastQC - {html_file.stem}",
                    "path": f"fastqc_out/{html_file.name}",
                    "type": "html",
                    "description": f"Individual FastQC report for {html_file.stem}"
                })
    
    # Check qc_trimmed results
    qc_trimmed_dir = run_dir / "qc_trimmed"
    if qc_trimmed_dir.exists():
        multiqc_html = qc_trimmed_dir / "multiqc_out" / "multiqc_report.html"
        fastqc_dir = qc_trimmed_dir / "fastqc_out"
        done_flag = qc_trimmed_dir / "qc_trimmed_done.flag"
        
        qc_results["qc_trimmed"] = {
            "completed": done_flag.exists(),
            "multiqc_available": multiqc_html.exists(),
            "fastqc_available": fastqc_dir.exists() and any(fastqc_dir.glob("*.html")),
            "files": []
        }
        
        # List available files
        if multiqc_html.exists():
            qc_results["qc_trimmed"]["files"].append({
                "name": "MultiQC Report",
                "path": "multiqc_out/multiqc_report.html",
                "type": "html",
                "description": "Aggregated quality control report"
            })
        
        # Check for additional MultiQC reports
        multiqc_dir = qc_trimmed_dir / "multiqc_out"
        if multiqc_dir.exists():
            for multiqc_file in multiqc_dir.glob("multiqc_report*.html"):
                if multiqc_file.name != "multiqc_report.html":  # Skip the main one we already added
                    qc_results["qc_trimmed"]["files"].append({
                        "name": f"MultiQC Report ({multiqc_file.stem})",
                        "path": f"multiqc_out/{multiqc_file.name}",
                        "type": "html",
                        "description": f"Additional MultiQC report: {multiqc_file.name}"
                    })
        
        if fastqc_dir.exists():
            for html_file in fastqc_dir.glob("*.html"):
                qc_results["qc_trimmed"]["files"].append({
                    "name": f"FastQC - {html_file.stem}",
                    "path": f"fastqc_out/{html_file.name}",
                    "type": "html",
                    "description": f"Individual FastQC report for {html_file.stem}"
                })
    
    return qc_results


@app.get("/runs/{run_id}/qc/{stage}/{file_path:path}")
async def get_qc_file(run_id: str, stage: str, file_path: str):
    """Serve QC result files (HTML reports, etc.)."""
    # Verify run exists
    state = load_run_state(run_id, Config.RUNS_DIR)
    if "error" in state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Validate stage
    if stage not in ["qc_raw", "qc_trimmed"]:
        raise HTTPException(status_code=400, detail=f"Invalid QC stage: {stage}")
    
    run_dir = Config.RUNS_DIR / run_id
    qc_dir = run_dir / stage
    
    # Construct full file path and validate it's within the QC directory
    full_file_path = (qc_dir / file_path).resolve()
    qc_dir_resolved = qc_dir.resolve()
    
    # Security check: ensure the file is within the QC directory
    if not str(full_file_path).startswith(str(qc_dir_resolved)):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    if not full_file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    # Determine content type based on file extension
    if file_path.endswith('.html'):
        # For HTML files, serve as HTML response
        with open(full_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    elif file_path.endswith(('.png', '.jpg', '.jpeg')):
        return FileResponse(path=full_file_path, media_type="image/*")
    elif file_path.endswith('.css'):
        return FileResponse(path=full_file_path, media_type="text/css")
    elif file_path.endswith('.js'):
        return FileResponse(path=full_file_path, media_type="application/javascript")
    else:
        return FileResponse(path=full_file_path, media_type="application/octet-stream")


@app.put("/runs/{run_id}/adapter")
async def update_adapter_type(run_id: str, adapter_data: Dict[str, str]):
    """Update adapter type for a run based on QC results."""
    # Verify run exists
    state = load_run_state(run_id, Config.RUNS_DIR)
    if "error" in state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    adapter_type = adapter_data.get("adapter_type")
    if not adapter_type:
        raise HTTPException(status_code=400, detail="adapter_type is required")
    
    # Validate adapter type
    valid_adapters = [
        'NexteraPE-PE', 'TruSeq2-PE', 'TruSeq2-SE', 
        'TruSeq3-PE', 'TruSeq3-PE-2', 'TruSeq3-SE'
    ]
    if adapter_type not in valid_adapters:
        raise HTTPException(status_code=400, detail=f"Invalid adapter type. Valid options: {valid_adapters}")
    
    # Update run parameters
    if "parameters" not in state:
        state["parameters"] = {}
    state["parameters"]["adapter_type"] = adapter_type
    state["updated_at"] = datetime.now().isoformat()
    
    # Save updated state
    save_run_state(run_id, state, Config.RUNS_DIR)
    
    return SuccessResponse(
        message=f"Adapter type updated to {adapter_type}",
        data={"adapter_type": adapter_type}
    )


@app.get("/runs/{run_id}/results/{result_type}")
async def get_results(run_id: str, result_type: str):
    """Download results files from a completed run."""
    # Verify run exists
    state = load_run_state(run_id, Config.RUNS_DIR)
    if "error" in state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    run_dir = Config.RUNS_DIR / run_id
    
    # Map result types to file paths
    result_files = {
        "counts_matrix": run_dir / "counts" / "deseq_counts_matrix.csv",
        "de_results": run_dir / "de" / "full_results.csv", 
        "top_degs": run_dir / "de" / "top_degs.csv",
        "summary_stats": run_dir / "summaries" / "trim_star_summary.csv",
        "qc_raw": run_dir / "qc_raw" / "multiqc_out" / "multiqc_report.html",
        "qc_trimmed": run_dir / "qc_trimmed" / "multiqc_out" / "multiqc_report.html"
    }
    
    if result_type not in result_files:
        raise HTTPException(status_code=400, detail=f"Invalid result type: {result_type}")
    
    file_path = result_files[result_type]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Result file not found: {result_type}")
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@app.get("/runs/{run_id}/featurecounts-summary")
async def get_featurecounts_summary(run_id: str):
    """
    Get featureCounts summary statistics.
    Returns the counts.txt.summary file content as JSON for easy display.
    """
    run_dir = Config.RUNS_DIR / run_id
    
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    summary_file = run_dir / "featurecounts" / "counts.txt.summary"
    
    if not summary_file.exists():
        raise HTTPException(
            status_code=404, 
            detail="featureCounts summary not found. Run the featureCounts stage first."
        )
    
    # Parse the summary file
    try:
        with open(summary_file, 'r') as f:
            lines = f.readlines()
        
        # First line contains headers (Status + sample names)
        headers = lines[0].strip().split('\t')
        status_label = headers[0]  # Should be "Status"
        sample_names = [Path(h).stem.replace('_Aligned.sortedByCoord.out', '') for h in headers[1:]]
        
        # Parse data rows
        stats = []
        for line in lines[1:]:
            parts = line.strip().split('\t')
            if len(parts) > 1:
                stat_name = parts[0]
                values = [int(v) for v in parts[1:]]
                stats.append({
                    "category": stat_name,
                    "samples": dict(zip(sample_names, values))
                })
        
        return {
            "summary": stats,
            "sample_names": sample_names,
            "file_path": str(summary_file)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing featureCounts summary: {str(e)}"
        )


@app.get("/runs/{run_id}/deseq2-results")
async def get_deseq2_results(run_id: str):
    """
    Get DESeq2 analysis results including summary and significant DEGs.
    Returns summary statistics, significant DEGs, and file paths for downloads.
    """
    run_dir = Config.RUNS_DIR / run_id
    
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    deseq2_dir = run_dir / "deseq2"
    
    if not deseq2_dir.exists():
        raise HTTPException(
            status_code=404, 
            detail="DESeq2 results not found. Run the DESeq2 stage first."
        )
    
    summary_file = deseq2_dir / "summary.txt"
    significant_degs_file = deseq2_dir / "significant_degs.csv"
    
    if not summary_file.exists():
        raise HTTPException(
            status_code=404,
            detail="DESeq2 summary not found."
        )
    
    try:
        # Parse summary file
        summary_data = {}
        with open(summary_file, 'r') as f:
            content = f.read()
            # Extract key statistics
            for line in content.split('\n'):
                if ':' in line and '=' not in line:
                    key, value = line.split(':', 1)
                    summary_data[key.strip()] = value.strip()
        
        # Parse significant DEGs if available
        significant_degs = []
        if significant_degs_file.exists():
            import pandas as pd
            df = pd.read_csv(significant_degs_file)
            # Convert to list of dicts for JSON serialization
            significant_degs = df.to_dict('records')
            # Round numeric values for display
            for deg in significant_degs:
                for key in ['baseMean', 'log2FoldChange', 'lfcSE', 'stat']:
                    if key in deg and pd.notna(deg[key]):
                        deg[key] = round(float(deg[key]), 4)
                for key in ['pvalue', 'padj']:
                    if key in deg and pd.notna(deg[key]):
                        deg[key] = float(deg[key])
        
        # Available files for download
        available_files = {
            "summary": str(summary_file) if summary_file.exists() else None,
            "significant_degs": str(significant_degs_file) if significant_degs_file.exists() else None,
            "full_results": str(deseq2_dir / "full_results.csv") if (deseq2_dir / "full_results.csv").exists() else None,
            "top_degs": str(deseq2_dir / "top_degs.csv") if (deseq2_dir / "top_degs.csv").exists() else None,
            "counts_matrix": str(deseq2_dir / "counts_matrix.csv") if (deseq2_dir / "counts_matrix.csv").exists() else None,
        }
        
        return {
            "summary": summary_data,
            "significant_degs": significant_degs,
            "num_significant": len(significant_degs),
            "available_files": available_files
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing DESeq2 results: {str(e)}"
        )


@app.get("/runs/{run_id}/deseq2-download/{file_type}")
async def download_deseq2_file(run_id: str, file_type: str):
    """
    Download a specific DESeq2 output file.
    file_type can be: summary, significant_degs, full_results, top_degs, counts_matrix
    """
    run_dir = Config.RUNS_DIR / run_id
    deseq2_dir = run_dir / "deseq2"
    
    if not deseq2_dir.exists():
        raise HTTPException(status_code=404, detail="DESeq2 results not found")
    
    file_map = {
        "summary": deseq2_dir / "summary.txt",
        "significant_degs": deseq2_dir / "significant_degs.csv",
        "full_results": deseq2_dir / "full_results.csv",
        "top_degs": deseq2_dir / "top_degs.csv",
        "counts_matrix": deseq2_dir / "counts_matrix.csv",
    }
    
    if file_type not in file_map:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file_type}")
    
    file_path = file_map[file_type]
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_type}")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="text/plain" if file_type == "summary" else "text/csv"
    )


@app.delete("/runs/{run_id}")
async def delete_run(run_id: str):
    """Delete a pipeline run and all associated data."""
    run_dir = Config.RUNS_DIR / run_id
    
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Remove run directory
    shutil.rmtree(run_dir)
    
    return SuccessResponse(message=f"Run {run_id} deleted successfully")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    #uvicorn.run(app, host="0.0.0.0", port=7080)