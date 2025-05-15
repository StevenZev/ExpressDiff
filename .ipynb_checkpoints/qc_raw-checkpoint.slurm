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

# Clean up previous outputs
## rm -rf qc_logs/*
rm -rf raw_fastqc_out/*
rm -rf raw_multiqc_out/*


# Create necessary output directories
mkdir -p raw_fastqc_out
mkdir -p raw_multiqc_out
mkdir -p ./qc_logs

# Load FastQC and MultiQC modules (adjust module names as required by your HPC system)
module load fastqc
module load multiqc

echo "Starting FastQC analysis for FASTQ files in ./raw_reads/"

# Loop over all .fq.gz files in the raw_reads directory and run FastQC
for fq in ./raw_reads/*.fq.gz; do
    echo "Processing file: ${fq}"
    fastqc -o raw_fastqc_out "${fq}"
done

echo "FastQC analysis complete. Running MultiQC to aggregate the reports."

# Run MultiQC on the FastQC output directory
multiqc -o raw_multiqc_out raw_fastqc_out

echo "MultiQC aggregation complete. All outputs are saved in raw_fastqc_out/ and raw_multiqc_out/"

touch qc_logs/fastqc_multiqc_done.flag

echo "Created completion flag."