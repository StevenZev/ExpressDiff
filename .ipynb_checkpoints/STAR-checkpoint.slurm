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
#SBATCH --error=./STAR_logs/slurm_STAR_%j.err

set -euo pipefail
module load star
module load parallel
mkdir -p STAR_logs STAR_out STAR_out/genome_index

# ---------- Setup ----------
READ_DIR=trimmed_reads
GENOME_DIR=mapping_in
STAR_INDEX=STAR_out/genome_index
OUT_DIR=STAR_out

FASTA=$(find "$GENOME_DIR" -name "*.fa" | head -n 1)
GTF=$(find "$GENOME_DIR" -name "*.gtf" | head -n 1)

if [[ ! -f "$FASTA" || ! -f "$GTF" ]]; then
  echo "Missing .fa or .gtf in $GENOME_DIR — exiting." >&2
  exit 1
fi

# ---------- Index Build ----------
if [[ ! -f "$STAR_INDEX/SA" ]]; then
  echo "[*] Building STAR genome index..."
  STAR --runThreadN $SLURM_CPUS_PER_TASK \
       --runMode genomeGenerate \
       --genomeDir "$STAR_INDEX" \
       --genomeFastaFiles "$FASTA" \
       --sjdbGTFfile "$GTF" \
       --sjdbOverhang 99
else
  echo "[*] Genome index found — skipping build."
fi

# ---------- Alignment Function ----------
align_sample() {
  FWD=$1
  REV=${FWD/_forward_paired.fq.gz/_reverse_paired.fq.gz}
  BASENAME=$(basename "$FWD" _forward_paired.fq.gz)

  if [[ ! -f "$REV" ]]; then
    echo "[!] Skipping $BASENAME — reverse pair missing."
    return
  fi

  echo "[*] Aligning $BASENAME"
  STAR --runThreadN 2 \
       --genomeDir "$STAR_INDEX" \
       --readFilesIn "$FWD" "$REV" \
       --readFilesCommand zcat \
       --outSAMtype BAM SortedByCoordinate \
       --quantMode GeneCounts \
       --outFileNamePrefix "${OUT_DIR}/${BASENAME}_"
  echo "[✓] Done: $BASENAME"
}

export -f align_sample
export STAR_INDEX OUT_DIR

# ---------- Run Alignments in Parallel ----------
find "$READ_DIR" -name "*_forward_paired.fq.gz" | parallel --ungroup -j $((SLURM_CPUS_PER_TASK / 2)) align_sample

# ---------- Completion ----------
touch STAR_logs/star_alignment_done.flag
echo "All alignments complete."
