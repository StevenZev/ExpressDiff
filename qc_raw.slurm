#!/bin/bash
#SBATCH --job-name=FastQC_MultiQC
#SBATCH --time=01:00:00
#SBATCH --partition=standard
#SBATCH --account=rc_student-workers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --output=./qc_logs/fastqc_multiqc_%j.out
##SBATCH --error=./slurm_logs/fastqc_multiqc_%j.err

# Clean up previous outputs
rm -rf raw_fastqc_out/*
rm -rf raw_multiqc_out/*

# Create necessary output directories
mkdir -p raw_fastqc_out
mkdir -p raw_multiqc_out
mkdir -p ./qc_logs

# Load required modules
module load fastqc
module load multiqc
module load parallel  # Make sure GNU parallel is available

echo "Starting parallel FastQC analysis for FASTQ files in ./raw_reads/"

# Export FastQC command for GNU parallel
export FASTQC_OUT_DIR="raw_fastqc_out"
export THREADS_PER_FILE=1

# Run FastQC in parallel across all files (1 thread per file, 8 files max in parallel)
find ./raw_reads -name "*.fq.gz" | parallel -j $SLURM_CPUS_PER_TASK --halt now,fail=1 \
    "fastqc --threads ${THREADS_PER_FILE} -o ${FASTQC_OUT_DIR} {}"

echo "FastQC analysis complete. Running MultiQC to aggregate the reports."

# Run MultiQC on the FastQC output directory
multiqc -o raw_multiqc_out raw_fastqc_out

echo "MultiQC aggregation complete. All outputs are saved in raw_fastqc_out/ and raw_multiqc_out/"

# Flag for completion
touch qc_logs/fastqc_multiqc_done.flag

echo "Created completion flag."
