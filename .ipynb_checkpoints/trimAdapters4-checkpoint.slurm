#!/bin/bash

#SBATCH --job-name=BatchTrim
#SBATCH --time=06:00:00
#SBATCH --partition=standard
#SBATCH --account=rc_student-workers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --output=./trim_logs/slurm_%j.out

mkdir -p ./trim_logs/
mkdir -p ./trimmed_reads/

# Load Trimmomatic module
module load trimmomatic
module load parallel

# Pull user adapter selection
ADAPTER_NAME=$(cat selected_adapter.txt)
ADAPTER_FILE="/apps/software/standard/core/trimmomatic/0.39/adapters/${ADAPTER_NAME}.fa"

# Validate adapter file
if [ ! -f "$ADAPTER_FILE" ]; then
  echo "ERROR: Adapter file '$ADAPTER_FILE' does not exist."
  echo "Available options:"
  ls /apps/software/standard/core/trimmomatic/0.39/adapters/*.fa | xargs -n 1 basename | sed 's/\.fa$//'
  exit 1
fi

# Clear trimmed_reads/
rm -f ./trimmed_reads/*.fq.gz

# Trimming function
trim_pair() {
  FILE1=$1
  FILE2=${FILE1/_1.fq.gz/_2.fq.gz}
  BASE=$(basename "$FILE1" _1.fq.gz)
  
  echo "[START] Trimming ${BASE} on $(hostname) at $(date)" >&1

  java -Xmx16G -jar $EBROOTTRIMMOMATIC/trimmomatic-0.39.jar \
    PE -threads 2 \
    "$FILE1" "$FILE2" \
    "trimmed_reads/${BASE}_forward_paired.fq.gz" "trimmed_reads/${BASE}_forward_unpaired.fq.gz" \
    "trimmed_reads/${BASE}_reverse_paired.fq.gz" "trimmed_reads/${BASE}_reverse_unpaired.fq.gz" \
    ILLUMINACLIP:"$ADAPTER_FILE":2:30:10 \
    LEADING:3 TRAILING:3 SLIDINGWINDOW:4:20 MINLEN:36
}

export -f trim_pair
export ADAPTER_FILE
export EBROOTTRIMMOMATIC

# Run in parallel: 16 CPUs total / 2 threads per task = 8 concurrent jobs
find raw_reads -name "*_1.fq.gz" | parallel -j 8 trim_pair {}

# Final flag
touch trim_logs/trimming_done.flag
echo "Wrote completion flag"
