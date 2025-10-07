# Test Reference Genome Files - Comparison

## Overview
Created minimal test reference files for fast STAR testing without waiting for full genome indexing.

---

## File Comparison

| Feature | Test Reference | Real Reference (GRCm39) |
|---------|---------------|------------------------|
| **Genome Size** | 30 KB | 2.6 GB |
| **Chromosomes** | 3 | 20 + X, Y, MT |
| **Total Length** | 30,000 bp | 2.7 billion bp |
| **Genes** | 30 | ~55,000 |
| **GTF Size** | 14 KB | 868 MB |
| **STAR Index Time** | ~5 seconds | ~25 minutes |
| **STAR Index Size** | <1 MB | ~10 GB |
| **Alignment Time** | ~10 seconds/sample | ~5 minutes/sample |
| **Disk Usage** | <1 MB total | ~10 GB total |

---

## Files Created

### Test Reference
```
test_data/
├── test_genome.fa           (30 KB)  - 3 chromosomes, 10kb each
└── test_annotation.gtf      (14 KB)  - 30 genes with exons
```

### Structure

**test_genome.fa:**
- 3 chromosomes (chr1, chr2, chr3)
- 10,000 bp each
- ATCG repeating pattern (semi-random but reproducible)
- Valid FASTA format for STAR

**test_annotation.gtf:**
- 30 genes total (10 per chromosome)
- Each gene has:
  - 2 exons (realistic for RNA-seq)
  - Gene, transcript, and exon features
  - Protein-coding gene type
  - Unique gene IDs (GENE0001-GENE0030)
- Alternating strands (+/-)
- Non-overlapping genes
- Valid GTF format for featureCounts

---

## Usage

### Option 1: Per-Run Test Reference (Recommended)
Use test files for specific test runs without affecting production:

```bash
# For current test run
RUN_ID="550190eb-8233-49c7-844b-48caab4dc3f3"
cp test_data/test_* /scratch/vth3bk/ExpressDiff/runs/$RUN_ID/reference/
```

✅ **Already done for run `550190eb-8233-49c7-844b-48caab4dc3f3`**

### Option 2: Global Test Reference
Replace global reference (affects all new runs):

```bash
# Backup real reference first!
mv mapping_in mapping_in.backup

# Create new mapping_in with test files
mkdir -p mapping_in
cp test_data/test_* mapping_in/

# To restore:
# rm -rf mapping_in
# mv mapping_in.backup mapping_in
```

---

## Expected STAR Output

With test reference, STAR will:

1. ✅ **Index successfully** (5 seconds)
   ```
   genome_index/
   ├── SA (small)
   ├── SAindex (small)
   └── ... (total <1 MB)
   ```

2. ✅ **Align reads** (10 seconds per sample)
   ```
   sample_A_Aligned.sortedByCoord.out.bam
   sample_A_ReadsPerGene.out.tab
   sample_A_Log.final.out
   ```

3. ⚠️ **Low mapping rate expected**
   - Test FASTQ reads are random sequences
   - Test genome is tiny (30kb vs real 2.7Gb)
   - Most reads won't map (this is OK for testing!)
   - Purpose: Verify pipeline works, not biological accuracy

---

## Alignment Statistics Expected

```
Input Read Pairs: 1000
  Uniquely mapped: ~0-5 (0.0-0.5%)
  Mapped to multiple loci: 0
  Too many loci: 0
  Unmapped: too short: ~50
  Unmapped: other: ~950
```

This is **EXPECTED** because:
- Random test reads don't match our simple test genome
- Real data with real genome will have 80-95% mapping rate

---

## Verification

Check files are detected:

```bash
python3 << 'EOF'
from pathlib import Path
from backend.core.config import Config

run_id = "550190eb-8233-49c7-844b-48caab4dc3f3"
run_dir = Config.RUNS_DIR / run_id
ref_dir = run_dir / "reference"

fasta = list(ref_dir.glob("*.fa")) + list(ref_dir.glob("*.fasta"))
gtf = list(ref_dir.glob("*.gtf"))

print(f"FASTA: {[f.name for f in fasta]}")
print(f"GTF: {[f.name for f in gtf]}")
print(f"✅ Ready for STAR!" if (fasta and gtf) else "❌ Missing files")
EOF
```

---

## Benefits

✅ **Fast iteration** - Test full pipeline in minutes instead of hours
✅ **Low disk usage** - <1 MB vs 10+ GB
✅ **Same workflow** - Uses real STAR, real formats
✅ **Easy cleanup** - Delete tiny index quickly
✅ **Parallel testing** - Can run multiple test runs without disk issues

---

## Production Use

**For real analysis**, use the full reference:

```bash
# Already available at:
/home/vth3bk/Pipelinin/ExpressDiff/mapping_in/
├── GRCm39.primary_assembly.genome.fa  (2.6 GB)
└── gencode.vM32.annotation.gtf        (868 MB)
```

Just **don't copy test files** to the run's reference directory - STAR will use global files automatically.

---

## Next Steps

1. ✅ Test files created
2. ✅ Copied to run reference directory
3. 🚀 **Ready to submit STAR!**

Try submitting STAR now - it should:
- Validate successfully (finds test FASTA + GTF)
- Build index in ~5 seconds
- Align samples in ~10 seconds each
- Complete in <1 minute total!

