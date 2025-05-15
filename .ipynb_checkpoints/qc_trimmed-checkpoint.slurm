#!/bin/bash
#SBATCH --job-name=FastQC_MultiQC
#SBATCH --time=01:00:00
#SBATCH --partition=standard
#SBATCH --account=rc_student-workers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --output=./qc_logs/fastqc_multiqc_%j.out
##SBATCH --error=./slurm_logs/fastqc_multiqc_%j.err

# Create necessary output directories
mkdir -p trimmed_fastqc_out
mkdir -p trimmed_multiqc_out
mkdir -p ./qc_logs

# Load FastQC and MultiQC modules (adjust module names as required by your HPC system)
module load fastqc
module load multiqc

# Determine which files to process
if [[ "$1" == "-skip" ]]; then
    FILE_PATTERN="./trimmed_reads/*.fq.gz"
    echo "Skipping paired filter. Processing all .fq.gz files."
else
    FILE_PATTERN="./trimmed_reads/*_paired.fq.gz"
    echo "Default mode: Processing only *_paired.fq.gz files."
fi

echo "Starting FastQC analysis for files matching: $FILE_PATTERN"

# Loop over selected .fq.gz files and run FastQC
for fq in $FILE_PATTERN; do
    echo "Processing file: ${fq}"
    fastqc -o trimmed_fastqc_out "${fq}"
done

echo "FastQC analysis complete. Running MultiQC to aggregate the reports."

# Run MultiQC on the FastQC output directory
multiqc -o trimmed_multiqc_out trimmed_fastqc_out

echo "MultiQC aggregation complete. All outputs are saved in trimmed_fastqc_out/ and trimmed_multiqc_out/"
