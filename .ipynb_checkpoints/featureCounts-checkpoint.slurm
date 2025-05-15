#!/bin/bash
#SBATCH --job-name=featureCounts
#SBATCH --time=01:00:00
#SBATCH --partition=standard
#SBATCH --account=rc_student-workers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --output=featureCounts_logs/slurm_%j.out

mkdir -p featureCounts_logs
# Create output directory if it doesn't exist
mkdir -p featureCounts_out

rm featureCounts_out/*

# Load required modules (adjust as needed for your system)
echo "loading miniforge..."
module load miniforge
echo "miniforge loaded."


# conda install -c bioconda subread

conda activate testenv
echo "environment activated"

which featureCounts

# Take the first gtf file in case there are multiple...
GTF_FILE=$(ls mapping_in/*.gtf | head -n 1)  

if [ ! -f "$GTF_FILE" ]; then
  echo "No GTF file found in mapping_in/. Exiting."
  exit 1
fi

# Run featureCounts
featureCounts --verbose -a "$GTF_FILE" -o featureCounts_out/counts.txt -T 8 -t exon -g gene_id -p -s 2 STAR_out/*Aligned.sortedByCoord.out.bam


touch featureCounts_logs/featurecounts_done.flag
echo "Wrote completion flag."