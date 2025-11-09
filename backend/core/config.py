"""
Configuration settings for ExpressDiff backend.
Python 3.6 compatible version.
"""
import os
from pathlib import Path
from typing import List, Dict


class Config:
    """Application configuration.

    In module-based deployments, code is installed in a shared, read-only
    location ("install dir"), while user data (runs, uploads, results) must
    live in a per-user writable work directory on scratch storage.

    Install dir is detected from EBROOTEXPRESSDIFF/EXPRESSDIFF_HOME or by
    walking up from this file. The work directory should be on the cluster
    scratch for the user: $SCRATCH (i.e., /scratch/$USER). For development
    convenience, if EXPRESSDIFF_WORKDIR is explicitly set, it will be used.
    No $HOME automatic fallback is allowed.
    """

    # Install (read-only) directory containing code, templates, and scripts
    # Prefer EasyBuild-provided root when available
    INSTALL_DIR = Path(
        os.environ.get(
            "EBROOTEXPRESSDIFF",
            os.environ.get(
                "EXPRESSDIFF_HOME",
                str(Path(__file__).resolve().parents[2])  # repo root when run from source
            ),
        )
    )

    @staticmethod
    def _default_workdir() -> Path:
        # 1) Explicit override for development (use with caution)
        env = os.environ.get("EXPRESSDIFF_WORKDIR")
        if env:
            return Path(env)
        # 2) Preferred: cluster scratch
        scratch = os.environ.get("SCRATCH")
        if scratch:
            return Path(scratch)
        # 3) No default fallback; force correct environment
        raise RuntimeError(
            "Work directory is not configured. Set EXPRESSDIFF_WORKDIR explicitly or ensure SCRATCH is set "
            "(preferred /scratch/$USER). No $HOME fallback is allowed."
        )

    # Per-user working directory for all run data
    BASE_DIR = _default_workdir.__func__()  # call without instance
    RUNS_DIR = BASE_DIR / "runs"
    
    # SLURM script mappings (relative to BASE_DIR)
    SLURM_SCRIPTS = {
        # Absolute paths to scripts installed with the module
        "qc_raw": str(INSTALL_DIR / "qc_raw.slurm"),
        "trim": str(INSTALL_DIR / "trimAdapters4.slurm"),
        "qc_trimmed": str(INSTALL_DIR / "qc_trimmed.slurm"),
        "star": str(INSTALL_DIR / "STAR.slurm"),
        "featurecounts": str(INSTALL_DIR / "featureCounts.slurm"),
        "deseq2": str(INSTALL_DIR / "deseq2.slurm"),
    }
    
    # Stage completion flags (relative to runs/{run_id}/)
    STAGE_FLAGS = {
        "qc_raw": "qc_raw/qc_raw_done.flag",
        "trim": "trimmed/trimming_done.flag",
        "qc_trimmed": "qc_trimmed/qc_trimmed_done.flag",
        "star": "star/star_alignment_done.flag",
        "featurecounts": "featurecounts/featurecounts_done.flag",
        "deseq2": "logs/deseq2_done.flag"
    }
    
    # Available adapter types for trimming
    ADAPTER_TYPES = [
        "NexteraPE-PE",
        "TruSeq2-PE", 
        "TruSeq2-SE",
        "TruSeq3-PE-2",
        "TruSeq3-PE",
        "TruSeq3-SE"
    ]
    
    # Pipeline stage dependencies
    STAGE_DEPENDENCIES = {
        "qc_raw": [],
        "trim": ["qc_raw"],
        "qc_trimmed": ["trim"],
        "star": ["trim"],
        "featurecounts": ["star"],
        "deseq2": ["featurecounts"]
    }
    
    # Default SLURM resource settings
    DEFAULT_RESOURCES = {
        "qc_raw": {"cpus": 8, "memory": "16G", "time": "01:00:00"},
        "trim": {"cpus": 16, "memory": "64G", "time": "06:00:00"},
        "qc_trimmed": {"cpus": 4, "memory": "8G", "time": "01:00:00"},
        "star": {"cpus": 8, "memory": "64G", "time": "08:00:00"},
        "featurecounts": {"cpus": 8, "memory": "16G", "time": "01:00:00"},
        "deseq2": {"cpus": 4, "memory": "16G", "time": "01:00:00"}
    }
    
    # API settings
    MAX_UPLOAD_SIZE = 1000 * 1024 * 1024  # 1GB in bytes
    ALLOWED_EXTENSIONS = {".fq.gz", ".fastq.gz", ".fa", ".gtf", ".csv", ".tsv"}
    
    # Reference data directory (user-provided references live in work dir)
    REFERENCE_DIR = BASE_DIR / "mapping_in"