"""
Pydantic models for ExpressDiff API request/response validation.
Python 3.6 compatible version.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class StageStatus(str, Enum):
    """Pipeline stage status enumeration."""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunStatus(str, Enum):
    """Overall pipeline run status."""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AdapterType(str, Enum):
    """Available adapter types for trimming."""
    NEXTERA_PE = "NexteraPE-PE"
    TRUESEQ2_PE = "TruSeq2-PE"
    TRUESEQ2_SE = "TruSeq2-SE"
    TRUESEQ3_PE_2 = "TruSeq3-PE-2"
    TRUESEQ3_PE = "TruSeq3-PE"
    TRUESEQ3_SE = "TruSeq3-SE"


class StageInfo(BaseModel):
    """Information about a pipeline stage."""
    status: StageStatus = StageStatus.PENDING
    job_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None


class RunCreate(BaseModel):
    """Request model for creating a new pipeline run."""
    name: Optional[str] = Field(None, description="Optional human-readable name for the run")
    description: Optional[str] = Field(None, description="Optional description")
    adapter_type: AdapterType = Field(AdapterType.NEXTERA_PE, description="Adapter type for trimming")
    account: str = Field(..., description="SLURM account to charge")


class RunInfo(BaseModel):
    """Complete information about a pipeline run."""
    run_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    status: RunStatus = RunStatus.CREATED
    created_at: datetime
    updated_at: Optional[datetime] = None
    stages: Dict[str, StageInfo] = {}
    parameters: Dict[str, Any] = {}
    account: str


class StageSubmit(BaseModel):
    """Request model for submitting a pipeline stage."""
    account: str = Field(..., description="SLURM account to charge")
    force: bool = Field(False, description="Force submission even if dependencies not met")
    confirm_rerun: bool = Field(False, description="Confirm re-running a completed stage (will overwrite previous results)")


class JobStatus(BaseModel):
    """SLURM job status information."""
    job_id: str
    state: str
    time: Optional[str] = None
    exit_code: Optional[str] = None
    error: Optional[str] = None


class FileUpload(BaseModel):
    """File upload information."""
    filename: str
    size: int
    content_type: Optional[str] = None


class SamplePair(BaseModel):
    """Paired-end sample information."""
    sample_name: str
    forward_file: str
    reverse_file: str
    valid: bool = True
    issues: List[str] = []


class SampleValidation(BaseModel):
    """Sample pairing validation results."""
    total_files: int
    valid_pairs: List[SamplePair]
    unpaired_files: List[str]
    issues: List[str] = []


class MetadataInfo(BaseModel):
    """Metadata file information."""
    filename: str
    samples: List[str]
    conditions: List[str]
    design_factors: List[str]
    sample_count: int


class DESeqParams(BaseModel):
    """Parameters for differential expression analysis."""
    design: str = Field("~condition", description="DESeq2 design formula")
    factor: str = Field("condition", description="Factor for contrast")
    reference_level: str = Field(..., description="Reference level for comparison")
    test_level: str = Field(..., description="Test level for comparison")
    alpha: float = Field(0.05, ge=0.01, le=0.1, description="Significance threshold")
    lfc_threshold: float = Field(1.0, ge=0.0, description="Log2 fold change threshold")

    @validator('design')
    def validate_design(cls, v):
        if not v.startswith('~'):
            raise ValueError("Design formula must start with '~'")
        return v


class DESeqResults(BaseModel):
    """Differential expression analysis results."""
    total_genes: int
    significant_genes: int
    upregulated: int
    downregulated: int
    results_file: str
    top_degs_file: Optional[str] = None


class PipelineStages(BaseModel):
    """Available pipeline stages and their status."""
    stages: List[str] = [
        "qc_raw",
        "trim", 
        "qc_trimmed",
        "star",
        "featurecounts",
        "deseq2"
    ]


class HealthCheck(BaseModel):
    """API health check response."""
    status: str = "healthy"  # Changed from Literal to str for Python 3.6
    timestamp: datetime
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None