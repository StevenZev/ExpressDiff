#!/bin/bash
#SBATCH --job-name=STAR_Align
#SBATCH --time=08:00:00
#SBATCH --partition=standard
#SBATCH --account=rc_student-workers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --output=./STAR_logs/slurm_STAR_%j.out

# ---------------------- Setup ----------------------

# Directories
READ_DIR=trimmed_reads
GENOME_DIR=mapping_in
STAR_INDEX=STAR_out/genome_index
OUT_DIR=STAR_out
mkdir -p "$OUT_DIR"
mkdir -p "$STAR_INDEX"
mkdir -p STAR_logs

# ---------------------- Reference Files ----------------------

# Get genome FASTA and GTF file
FASTA=$(find "$GENOME_DIR" -name "*.fa" | head -n 1)
GTF=$(find "$GENOME_DIR" -name "*.gtf" | head -n 1)

# Check they exist
if [[ ! -f "$FASTA" || ! -f "$GTF" ]]; then
  echo "ERROR: Missing .fa or .gtf file in $GENOME_DIR. Exiting."
  exit 1
fi

echo "Using FASTA: $FASTA"
echo "Using GTF: $GTF"

# ---------------------- Load STAR ----------------------

module load star
set -e  # Exit on error
set -x  # Echo commands

# ---------------------- Index Build ----------------------

if [ ! -f "$STAR_INDEX/SA" ]; then
  echo "Building STAR genome index..."
  STAR --runThreadN 8 \
       --runMode genomeGenerate \
       --genomeDir "$STAR_INDEX" \
       --genomeFastaFiles "$FASTA" \
       --sjdbGTFfile "$GTF" \
       --sjdbOverhang 99
else
  echo "STAR index already exists — skipping build."
fi

# ---------------------- Align Trimmed Reads ----------------------

FILES=($(ls ${READ_DIR}/*_forward_paired.fq.gz))

for FWD in "${FILES[@]}"; do
  REV=${FWD/_forward_paired.fq.gz/_reverse_paired.fq.gz}
  BASENAME=$(basename "$FWD" _forward_paired.fq.gz)

  if [[ ! -f "$REV" ]]; then
    echo "WARNING: Missing reverse read for $FWD. Skipping $BASENAME..."
    continue
  fi

  echo "Aligning sample: $BASENAME"
  echo "FWD: $FWD"
  echo "REV: $REV"

  STAR --runThreadN 8 \
       --genomeDir "$STAR_INDEX" \
       --readFilesIn "$FWD" "$REV" \
       --readFilesCommand zcat \
       --outSAMtype BAM SortedByCoordinate \
       --quantMode GeneCounts \
       --outFileNamePrefix "${OUT_DIR}/${BASENAME}_"

  echo "Finished $BASENAME"
done

# ---------------------- Completion Flag ----------------------

touch STAR_logs/star_alignment_done.flag
echo "Wrote completion flag."

