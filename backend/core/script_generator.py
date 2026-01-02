"""
SLURM script generator for run-specific pipeline execution.
Generates customized SLURM scripts from templates with run-specific parameters.
In module deployments, templates live in the install directory, while generated
scripts are written to the user's work directory.
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Optional
from .config import Config


class SLURMScriptGenerator:
    """Generates run-specific SLURM scripts from templates."""

    def __init__(self, base_dir: Path = None, templates_dir: Path = None):
        # Per-user work directory for outputs
        self.base_dir = base_dir or Config.BASE_DIR
        # Templates always come from the read-only install directory by default
        self.templates_dir = templates_dir or (Config.INSTALL_DIR / "slurm_templates")
        # Generated scripts live in the user's work directory
        self.generated_scripts_dir = self.base_dir / "generated_slurm"
        
        # Ensure directories exist (create parents too)
        self.generated_scripts_dir.mkdir(parents=True, exist_ok=True)
        
        # Template mapping
        self.templates = {
            "qc_raw": "qc_raw.slurm.template",
            "trim": "trim.slurm.template", 
            "qc_trimmed": "qc_trimmed.slurm.template",
            "star": "star.slurm.template",
            "featurecounts": "featurecounts.slurm.template",
            "deseq2": "deseq2.slurm.template"
        }
    
    def generate_script(self, stage: str, run_id: str, account: str, 
                       adapter_type: str = "NexteraPE-PE") -> Path:
        """
        Generate a run-specific SLURM script from template.
        
        Args:
            stage: Pipeline stage name
            run_id: Unique run identifier
            account: SLURM account to charge
            adapter_type: Adapter type for trimming stage
            
        Returns:
            Path to generated script file
        """
        if stage not in self.templates:
            raise ValueError(f"Unknown stage: {stage}")
            
        template_path = self.templates_dir / self.templates[stage]
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        # Read template
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Replace placeholders using simple string replacement
        replacements = {
            '{RUN_ID}': run_id,
            '{ACCOUNT}': account,
            '{BASE_DIR}': str(self.base_dir),
            '{RUN_DIR}': str(self.base_dir / "runs" / run_id),
            '{ADAPTER_TYPE}': adapter_type
        }
        
        script_content = template_content
        for placeholder, value in replacements.items():
            script_content = script_content.replace(placeholder, value)
        
        # Generate output path
        script_filename = f"{stage}_{run_id}.slurm"
        script_path = self.generated_scripts_dir / script_filename
        
        # Write generated script
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(script_path, 0o755)
        
        return script_path
    
    def cleanup_run_scripts(self, run_id: str) -> None:
        """Remove all generated scripts for a specific run."""
        for script_path in self.generated_scripts_dir.glob(f"*_{run_id}.slurm"):
            script_path.unlink()
    
    def cleanup_old_scripts(self, keep_recent: int = 10) -> None:
        """Clean up old generated scripts, keeping only the most recent ones."""
        script_files = list(self.generated_scripts_dir.glob("*.slurm"))
        script_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove older scripts
        for script_path in script_files[keep_recent:]:
            script_path.unlink()


def get_script_generator() -> SLURMScriptGenerator:
    """Get a configured script generator instance."""
    return SLURMScriptGenerator()