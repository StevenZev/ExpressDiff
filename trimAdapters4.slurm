#!/bin/bash

#SBATCH --job-name=BatchTrim
#SBATCH --time=06:00:00
#SBATCH --partition=standard
#SBATCH --account=rc_student-workers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G

#SBATCH --output=./trim_logs/slurm_%j.out
mkdir -p ./trim_logs/

# Pull user adapter selection
ADAPTER_NAME=$(cat selected_adapter.txt)

echo "Using adapter: $ADAPTER"

# Check if an argument was passed
if [ $# -gt 0 ]; then
  ADAPTER_NAME="$1"
fi

# Construct full adapter path
ADAPTER_FILE="/apps/software/standard/core/trimmomatic/0.39/adapters/${ADAPTER_NAME}.fa"

# Check if adapter file exists
if [ ! -f "$ADAPTER_FILE" ]; then
  echo "ERROR: Adapter file '$ADAPTER_FILE' does not exist."
  echo "Please use one of the available options:"
  ls /apps/software/standard/core/trimmomatic/0.39/adapters/*.fa | xargs -n 1 basename | sed 's/\.fa$//'
  exit 1
fi


# Define input and output directories
INPUT_DIR=./raw_reads/
OUTPUT_DIR=./trimmed_reads/

echo "Clearing trimmed_reads directory."
rm -f ${OUTPUT_DIR}/*.fq.gz

# Load Trimmomatic module
module load trimmomatic
echo "Using adapter file: $ADAPTER_FILE"

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# Collect all forward read files into an array
FILES=($(ls ${INPUT_DIR}*_1.fq.gz))

# Loop over each file pair
for FILE1 in "${FILES[@]}"; do
  FILE2=${FILE1/_1.fq.gz/_2.fq.gz}
  BASE=$(basename "$FILE1" _1.fq.gz)

  echo "Processing file pair: $FILE1 and $FILE2"

  java -Xmx16G -jar $EBROOTTRIMMOMATIC/trimmomatic-0.39.jar \
    PE -threads 8 \
    "$FILE1" "$FILE2" \
    "${OUTPUT_DIR}/${BASE}_forward_paired.fq.gz" "${OUTPUT_DIR}/${BASE}_forward_unpaired.fq.gz" \
    "${OUTPUT_DIR}/${BASE}_reverse_paired.fq.gz" "${OUTPUT_DIR}/${BASE}_reverse_unpaired.fq.gz" \
    ILLUMINACLIP:"$ADAPTER_FILE":2:30:10 \
    LEADING:3 TRAILING:3 SLIDINGWINDOW:4:20 MINLEN:36

  echo "Trimming complete for ${BASE}"
  
  
done

touch trim_logs/trimming_done.flag
echo "Wrote completion flag"
