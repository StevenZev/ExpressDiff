# ExpressDiff Demo - Quick Start Guide

## Preparation (5 minutes)

### Generate Demo Data
```bash
cd /home/vth3bk/Pipelinin/ExpressDiff
python3 create_demo_data.py
```

This creates:
- **Reference files**: demo_reference/demo_genome.fa, demo_reference/demo_annotation.gtf
- **6 samples**: 3 control + 3 treatment (12 FASTQ files total)
- **~50K reads per sample**: Realistic but fast to process

---

## Demo Workflow (10 minutes)

### 1. Start ExpressDiff (if not running)
```bash
cd /home/vth3bk/Pipelinin/ExpressDiff
source .env
./launch_expressdiff.sh
```

Access at: http://localhost:3000

### 2. Create New Run
- Click "Create New Run"
- **Name**: "Demo: Control vs Treatment"
- **Description**: "Synthetic RNA-seq data with 100 genes showing differential expression"
- **Account**: rc_student-workers (or your account)
- **Adapter**: NexteraPE-PE
- Click "Create Run"

### 3. Upload Reference Files
- Click on your new run
- Go to "Upload" tab
- Select **Reference Files**
- Upload:
  - `demo_reference/demo_genome.fa`
  - `demo_reference/demo_annotation.gtf`
- Wait for upload to complete

### 4. Upload Sample Files
- Still in "Upload" tab
- Select **FASTQ Files**
- Upload all 12 files from `demo_data/`:
  ```
  control_1_1.fq.gz      treatment_1_1.fq.gz
  control_1_2.fq.gz      treatment_1_2.fq.gz
  control_2_1.fq.gz      treatment_2_1.fq.gz
  control_2_2.fq.gz      treatment_2_2.fq.gz
  control_3_1.fq.gz      treatment_3_1.fq.gz
  control_3_2.fq.gz      treatment_3_2.fq.gz
  ```
- UI will auto-detect 6 sample pairs

### 5. Run Pipeline Stages

Go to "Pipeline" tab and run each stage in order:

#### Stage 1: QC Raw (~1 min)
- Click "Run" on "QC Raw Reads"
- Watch status change: Pending → Running → Completed
- View results in "Results" tab

#### Stage 2: Trimming (~2 min)
- Click "Run" on "Trim Adapters"
- Processes all 6 samples in parallel
- Creates trimmed FASTQ files

#### Stage 3: QC Trimmed (~1 min)
- Click "Run" on "QC Trimmed Reads"
- Compare quality before/after trimming

#### Stage 4: STAR Alignment (~3 min)
- Click "Run" on "STAR Alignment"
- Builds genome index (once)
- Aligns all 6 samples
- **Expected**: ~40-50% unique alignment

#### Stage 5: featureCounts (~1 min)
- Click "Run" on "featureCounts"
- Counts reads per gene (100 genes)
- Creates count matrix

#### Stage 6: DESeq2 (~1 min)
- Click "Run" on "DESeq2 Analysis"
- Differential expression analysis
- **Expected**: ~17-20 significant genes

**Total Runtime**: ~9-10 minutes

---

## Expected Results

### QC Results
- **FastQC**: All samples should show:
  - Per base quality: High (Phred 30-40)
  - Sequence duplication: Low-moderate
  - Adapter content: Minimal (clean synthetic reads)

### Alignment (STAR)
- **Uniquely mapped**: 40-50%
- **Multi-mapped**: ~5%
- **Unmapped**: 45-50%
  
*Note: Lower than real data because random intergenic regions don't align*

### Gene Counts
- **Total genes**: 100
- **Detected genes**: ~95-100
- **Average counts**: 400-600 per gene
- **Total counts per sample**: ~50K

### Differential Expression (DESeq2)
- **Significant genes** (padj < 0.05): ~17-20
  - **Upregulated**: ~8-10 genes (log2FC ~ +1)
  - **Downregulated**: ~8-10 genes (log2FC ~ -1)
- **Unchanged genes**: ~80

### Visualizations
- **Volcano Plot**: Clear separation of DE genes
- **MA Plot**: Treatment effect visible
- **Heatmap**: Samples cluster by condition
- **PCA**: Separation between control/treatment

---

## Demo Talking Points

### Introduction
*"Today I'll demonstrate ExpressDiff, a web-based RNA-seq analysis pipeline. I've generated synthetic data mimicking a real experiment: control vs treatment comparison with 100 genes and 6 samples."*

### During Upload
*"The system accepts standard FASTQ files and automatically detects paired-end samples. We're uploading 3 biological replicates per condition - essential for statistical power in RNA-seq."*

### During QC
*"ExpressDiff runs FastQC and MultiQC to assess sequencing quality. These reports show per-base quality scores, GC content, and adapter contamination - all critical quality metrics."*

### During Trimming
*"Trimmomatic removes low-quality bases and adapter sequences. This is crucial because poor quality reads reduce alignment accuracy."*

### During Alignment
*"STAR is the gold standard for RNA-seq alignment. It's splice-aware, meaning it correctly handles reads spanning exon-exon junctions. Our 40-50% alignment rate is expected for this synthetic data."*

### During Counting
*"featureCounts quantifies gene expression by counting how many reads map to each gene. This creates the count matrix needed for statistical analysis."*

### During DESeq2
*"DESeq2 performs rigorous statistical testing for differential expression. It accounts for biological variation and uses negative binomial distribution - appropriate for count data."*

### Results
*"As expected, we detected approximately 20 differentially expressed genes. These match our ground truth: we built 2-fold changes into the data, and DESeq2 successfully detected them. This validates the entire pipeline."*

---

## Troubleshooting

### Pipeline stage fails
- Check the "Logs" section in the stage card
- Common issues:
  - **QC/Trim**: Module not loaded (fastqc, trimmomatic)
  - **STAR**: Out of memory (need 8GB+)
  - **featureCounts**: Conda env not activated

### Low alignment rate (< 20%)
- Check if reference files uploaded correctly
- Verify FASTQ files aren't corrupted
- For demo data, 40-50% is expected and OK

### featureCounts finds no reads
- Check STAR completed successfully
- Verify BAM files have content (not just headers)
- Check strandedness setting matches data

### DESeq2 finds no significant genes
- Verify sample naming (control vs treatment)
- Check if enough replicates (need 3 per group)
- Look at PCA plot - are groups separated?

---

## Scaling Up

### For Longer Demo (30 minutes)
Edit `create_demo_data.py`:
```python
READS_PER_SAMPLE = 200000  # 200K reads
```
This gives:
- More realistic read depth
- Better counting statistics
- ~25-30 minute runtime

### For Production Use
Switch to real data:
- Upload your own FASTQ files
- Upload appropriate reference (GRCh38, GRCm39, etc.)
- Expect:
  - 70-90% alignment for good data
  - 20K+ genes quantified
  - 1-2 hour runtime for 6 samples

---

## Clean Up (Optional)

### Remove Demo Data
```bash
rm -rf demo_reference demo_data
```

### Archive Demo Run
- In UI, go to run details
- Click "Delete Run" (if implemented)
- Or leave it as an example

---

## Summary

✅ **Generated**: 100-gene reference + 6 RNA-seq samples  
✅ **Uploaded**: 14 files (2 reference + 12 FASTQ)  
✅ **Processed**: Full pipeline in ~10 minutes  
✅ **Detected**: ~20 differentially expressed genes  
✅ **Validated**: Pipeline works end-to-end  

**Perfect for demonstrations, teaching, and testing!**
