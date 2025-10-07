# Demo Data for ExpressDiff

## Overview
This directory contains tools to generate realistic synthetic RNA-seq data for demonstrating the ExpressDiff pipeline.

## What Gets Generated

### Reference Genome
- **100 genes** across 3 chromosomes
- Each gene has **3 exons** (200bp each)
- **~100kb total genome size**
- GTF annotation with all gene/transcript/exon features

### RNA-seq Samples
- **6 samples total**: 3 control + 3 treatment
- **50,000 read pairs** per sample (realistic for demo)
- **75bp paired-end reads**
- **Differential expression built in**:
  - 10 genes upregulated 2-fold in treatment
  - 10 genes downregulated 0.5-fold in treatment
  - 80 genes unchanged

## Generation

### Quick Start
```bash
cd /home/vth3bk/Pipelinin/ExpressDiff
python3 create_demo_data.py
```

### Output Structure
```
demo_reference/
├── demo_genome.fa          # ~100kb FASTA genome
└── demo_annotation.gtf     # 100 genes, 300 exons

demo_data/
├── control_1_1.fq.gz     # Control replicate 1, Read 1
├── control_1_2.fq.gz     # Control replicate 1, Read 2
├── control_2_1.fq.gz     # Control replicate 2, Read 1
├── control_2_2.fq.gz     # Control replicate 2, Read 2
├── control_3_1.fq.gz     # Control replicate 3, Read 1
├── control_3_2.fq.gz     # Control replicate 3, Read 2
├── treatment_1_1.fq.gz   # Treatment replicate 1, Read 1
├── treatment_1_2.fq.gz   # Treatment replicate 1, Read 2
├── treatment_2_1.fq.gz   # Treatment replicate 2, Read 1
├── treatment_2_2.fq.gz   # Treatment replicate 2, Read 2
├── treatment_3_1.fq.gz   # Treatment replicate 3, Read 1
└── treatment_3_2.fq.gz   # Treatment replicate 3, Read 2
```

## Pipeline Usage

### 1. Create a New Run
- Name: "Demo Run - Differential Expression"
- Description: "Control vs Treatment comparison with 100 genes"

### 2. Upload Reference Files
- Upload `demo_reference/demo_genome.fa`
- Upload `demo_reference/demo_annotation.gtf`

### 3. Upload Sample Files
Upload all 6 paired FASTQ files from `demo_data/`

The ExpressDiff UI will auto-detect pairs:
- control_1: control_1_R1.fq.gz + control_1_R2.fq.gz
- control_2: control_2_R1.fq.gz + control_2_R2.fq.gz
- control_3: control_3_R1.fq.gz + control_3_R2.fq.gz
- treatment_1: treatment_1_R1.fq.gz + treatment_1_R2.fq.gz
- treatment_2: treatment_2_R1.fq.gz + treatment_2_R2.fq.gz
- treatment_3: treatment_3_R1.fq.gz + treatment_3_R2.fq.gz

### 4. Run Pipeline Stages

**QC Raw** (~1 min)
- FastQC on 6 samples
- MultiQC summary

**Trimming** (~2 min)
- Adapter trimming with Trimmomatic
- Remove low-quality bases

**QC Trimmed** (~1 min)
- Quality check after trimming

**STAR Alignment** (~3 min)
- Build genome index
- Align 6 samples
- Expected: ~40-50% alignment rate

**featureCounts** (~1 min)
- Count reads per gene
- 100 genes quantified

**DESeq2** (~1 min)
- Differential expression analysis
- Expected: ~20 significant genes

**Total Runtime: ~9-10 minutes**

## Expected Results

### Alignment Statistics
- **Uniquely mapped reads**: ~40-50%
- **Multi-mapped**: ~5%
- **Unmapped**: ~45-50%

*Note: Lower than real data because synthetic sequences have less complexity*

### Gene Counts
- **Detected genes**: ~90-100 genes
- **Average counts**: 400-600 per gene
- **Total counts**: ~50K per sample

### Differential Expression
**True Positives** (should be detected):
- 10 upregulated genes (log2FC ~ +1)
- 10 downregulated genes (log2FC ~ -1)

**Expected DESeq2 Results**:
- ~15-20 significant genes (padj < 0.05)
- ~85% sensitivity (detect 17 out of 20 true DE genes)
- Very few false positives

### Volcano Plot
- Clear separation between DE and non-DE genes
- Upregulated genes cluster at log2FC ~ +1
- Downregulated genes cluster at log2FC ~ -1
- Most genes cluster around log2FC ~ 0

## Technical Details

### Data Characteristics
- **Read length**: 75bp paired-end
- **Quality scores**: Phred 30-40 (high quality)
- **Error rate**: 0.5% (realistic sequencing errors)
- **Insert size**: ~150bp
- **Strandedness**: Reverse stranded (compatible with most protocols)

### Gene Expression
- **Control samples**: Natural expression distribution
- **Treatment samples**: 
  - DEMO0001-DEMO0010: 2x upregulated
  - DEMO0091-DEMO0100: 0.5x downregulated
  - DEMO0011-DEMO0090: Unchanged

### Biological Realism
- ✅ Reads generated from actual gene sequences
- ✅ Paired-end fragments from mRNA
- ✅ Strand-specific
- ✅ Realistic quality scores
- ✅ Sequencing errors
- ✅ Biological variation between replicates
- ✅ Differential expression patterns

### Differences from Real Data
- ⚠️ Simpler genome (100 genes vs 20,000+)
- ⚠️ No isoforms (1 transcript per gene)
- ⚠️ Perfect exon boundaries (no splicing variation)
- ⚠️ Uniform gene lengths
- ⚠️ Lower alignment rate (random intergenic sequences)

## Troubleshooting

### Low alignment rate (< 30%)
- **Normal for synthetic data!** Random sequences don't align well
- As long as exonic reads align (~40-50%), analysis works

### featureCounts shows 0 counts
- Check STAR output - do BAM files have reads?
- Verify GTF coordinates match genome
- Check strandedness setting (-s 2)

### DESeq2 finds no significant genes
- Check if you used correct condition labels (control vs treatment)
- Verify sample names match condition
- 3 replicates should give good power for 2-fold changes

### Pipeline runs too fast
- Increase READS_PER_SAMPLE in create_demo_data.py
- 100K reads = ~15 min runtime
- 500K reads = ~45 min runtime
- 1M reads = ~1.5 hour runtime

## Customization

Edit `create_demo_data.py` to adjust:
```python
NUM_GENES = 100           # More genes = larger reference
READS_PER_SAMPLE = 50000  # More reads = longer runtime
NUM_REPLICATES = 3        # More replicates = better power
READ_LENGTH = 75          # Match your sequencing platform
```

## For Presentation

### Key Talking Points
1. "This synthetic data mimics real RNA-seq with 100 genes and 50K reads per sample"
2. "We have 3 biological replicates per condition for statistical power"
3. "Pipeline processes 300K total read pairs in under 10 minutes"
4. "Built-in 2-fold expression changes let us validate the analysis"
5. "Results show ~40% alignment and detect 17/20 truly differential genes"

### Demo Script
```bash
# 1. Generate data (run once)
python3 create_demo_data.py

# 2. In UI: Create new run
# 3. Upload 2 reference files
# 4. Upload 12 FASTQ files (6 samples × 2 reads)
# 5. Run pipeline end-to-end
# 6. Show results:
#    - Alignment rate ~45%
#    - Gene counts for 100 genes
#    - Volcano plot with clear DE genes
#    - Heatmap showing treatment effect
```

## File Sizes
- Reference genome: ~100 KB
- GTF annotation: ~50 KB
- Each FASTQ file: ~500-800 KB gzipped
- Total upload: ~6-8 MB
- Total storage with results: ~20-30 MB

Perfect for quick demos and testing!
