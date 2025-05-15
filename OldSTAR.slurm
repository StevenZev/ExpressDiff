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

# Directories
READ_DIR=trimmed_reads
GENOME_DIR=mapping_in
STAR_INDEX=STAR_out/genome_index
OUT_DIR=STAR_out

# Filenames
FASTA=${GENOME_DIR}/*.fa
GTF=${GENOME_DIR}/*.gtf

# Alternative input specification
FASTA=$(find "$GENOME_DIR" -name "*.fa" | head -n 1)
GTF=$(find "$GENOME_DIR" -name "*.gtf" | head -n 1)

if [[ ! -f "$FASTA" || ! -f "$GTF" ]]; then
  echo "Missing .fa or .gtf file in mapping_in/. Exiting."
  exit 1
fi

echo "Using FASTA: $FASTA"
echo "Using GTF: $GTF"




# Load STAR
module load star

# Make output directories
mkdir -p "$OUT_DIR"
mkdir -p "$STAR_INDEX"

# Only build index if not already built
if [ ! -f "$STAR_INDEX/SA" ]; then
  echo "Building STAR genome index..."
  STAR --runThreadN 8 \
       --runMode genomeGenerate \
       --genomeDir "$STAR_INDEX" \
       --genomeFastaFiles "$FASTA" \
       --sjdbGTFfile "$GTF" \
       --sjdbOverhang 99
else
  echo "STAR genome index already exists. Skipping indexing."
fi

# Align each paired file set
FILES=($(ls ${READ_DIR}/*_1.fq.gz))
for FWD in "${FILES[@]}"; do
  REV=${FWD/_1.fq.gz/_2.fq.gz}
  BASENAME=$(basename "$FWD" _1.fq.gz)

  echo "Aligning $BASENAME..."

  STAR --runThreadN 8 \
       --genomeDir "$STAR_INDEX" \
       --readFilesIn "$FWD" "$REV" \
       --readFilesCommand zcat \
       --outSAMtype BAM SortedByCoordinate \
       --quantMode GeneCounts \
       --outFileNamePrefix "${OUT_DIR}/${BASENAME}_"

  echo "Finished $BASENAME"
done

touch STAR_logs/star_alignment_done.flag
echo "Wrote completion flag."
