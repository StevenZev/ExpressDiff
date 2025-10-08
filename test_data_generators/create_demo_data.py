#!/usr/bin/env python3
"""
Create realistic synthetic RNA-seq data for ExpressDiff demo.

This generates:
- A small reference genome (100 genes, ~100kb total)
- Synthetic RNA-seq reads that actually align to the reference
- Differential expression between conditions (e.g., treatment vs control)
- Realistic sequencing depth (~50K reads per sample)

The data is small enough to run quickly (~5-10 min) but realistic enough to show:
- Successful alignment
- Gene counts
- Statistically significant differential expression
"""

import random
import gzip
from pathlib import Path

# Set random seed for reproducibility
random.seed(42)

# Configuration
NUM_GENES = 100
GENE_LENGTH = 1000  # Base pairs per gene
EXONS_PER_GENE = 3
EXON_LENGTH = 200
INTRON_LENGTH = 200
READS_PER_SAMPLE = 50000  # 50K reads per sample
READ_LENGTH = 75
NUM_REPLICATES = 3  # 3 replicates per condition

# Chromosomes
CHROMOSOMES = ['chr1', 'chr2', 'chr3']

# Base quality score (Phred+33)
def quality_string(length):
    """Generate quality scores (mostly high quality)."""
    # Phred scores 20-40 (Phred+33 encoding: 5-I in ASCII)
    # Most scores are high quality (35-40), with some variation
    quality_chars = '56789:;<=>?@ABCDEFGHI'  # Phred 21-40
    weights = [1, 1, 1, 2, 2, 3, 3, 4, 5, 5, 6, 7, 8, 10, 12, 15, 18, 20, 25, 30, 35]
    return ''.join(random.choices(quality_chars, weights=weights, k=length))

def random_sequence(length):
    """Generate random DNA sequence."""
    return ''.join(random.choices('ACGT', k=length))

def reverse_complement(seq):
    """Get reverse complement of DNA sequence."""
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
    return ''.join(complement[base] for base in reversed(seq))

def mutate_sequence(seq, error_rate=0.01):
    """Introduce sequencing errors."""
    seq_list = list(seq)
    for i in range(len(seq_list)):
        if random.random() < error_rate:
            seq_list[i] = random.choice('ACGT')
    return ''.join(seq_list)

class Gene:
    """Represents a gene with exons and introns."""
    def __init__(self, gene_id, chrom, start, strand):
        self.gene_id = gene_id
        self.chrom = chrom
        self.start = start
        self.strand = strand
        self.exons = []
        self.sequence = ""
        
        # Create gene structure
        current_pos = start
        for i in range(EXONS_PER_GENE):
            exon_start = current_pos
            exon_end = current_pos + EXON_LENGTH - 1
            self.exons.append((exon_start, exon_end))
            current_pos = exon_end + 1 + INTRON_LENGTH
        
        self.end = current_pos - INTRON_LENGTH - 1
        
        # Generate sequence for the entire gene region
        total_length = self.end - self.start + 1
        self.sequence = random_sequence(total_length)
    
    def get_exon_sequence(self):
        """Get concatenated exon sequence (mature mRNA)."""
        exon_seq = ""
        for exon_start, exon_end in self.exons:
            relative_start = exon_start - self.start
            relative_end = exon_end - self.start + 1
            exon_seq += self.sequence[relative_start:relative_end]
        return exon_seq
    
    def get_gtf_lines(self):
        """Generate GTF annotation lines."""
        lines = []
        # Gene line
        lines.append(f"{self.chrom}\tsynthetic\tgene\t{self.start}\t{self.end}\t.\t{self.strand}\t.\t"
                    f'gene_id "{self.gene_id}"; gene_name "{self.gene_id}";')
        # Transcript line
        transcript_id = f"{self.gene_id}_transcript"
        lines.append(f"{self.chrom}\tsynthetic\ttranscript\t{self.start}\t{self.end}\t.\t{self.strand}\t.\t"
                    f'gene_id "{self.gene_id}"; transcript_id "{transcript_id}";')
        # Exon lines
        for i, (exon_start, exon_end) in enumerate(self.exons, 1):
            lines.append(f"{self.chrom}\tsynthetic\texon\t{exon_start}\t{exon_end}\t.\t{self.strand}\t.\t"
                        f'gene_id "{self.gene_id}"; transcript_id "{transcript_id}"; exon_number "{i}";')
        return lines

def generate_reference_genome(genes, output_dir):
    """Generate reference genome FASTA and GTF files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create FASTA file
    fasta_path = output_dir / "demo_genome.fa"
    with open(fasta_path, 'w') as f:
        # Build chromosomes by concatenating genes
        chrom_sequences = {chrom: [] for chrom in CHROMOSOMES}
        chrom_genes = {chrom: [] for chrom in CHROMOSOMES}
        
        for gene in genes:
            chrom_genes[gene.chrom].append(gene)
        
        for chrom in CHROMOSOMES:
            # Sort genes by position
            chrom_genes[chrom].sort(key=lambda g: g.start)
            
            # Build chromosome sequence
            chrom_seq = "N" * 1000  # Start with some Ns
            last_end = 1000
            
            for gene in chrom_genes[chrom]:
                # Add intergenic region
                intergenic_length = gene.start - last_end - 1
                if intergenic_length > 0:
                    chrom_seq += random_sequence(intergenic_length)
                
                # Add gene sequence
                chrom_seq += gene.sequence
                last_end = gene.end
            
            # Add ending Ns
            chrom_seq += "N" * 1000
            
            # Write to FASTA
            f.write(f">{chrom}\n")
            # Write in 60-character lines
            for i in range(0, len(chrom_seq), 60):
                f.write(chrom_seq[i:i+60] + "\n")
    
    # Create GTF file
    gtf_path = output_dir / "demo_annotation.gtf"
    with open(gtf_path, 'w') as f:
        f.write("##description: Synthetic RNA-seq demo annotation\n")
        f.write("##provider: ExpressDiff\n")
        f.write("##format: gtf\n")
        for gene in genes:
            for line in gene.get_gtf_lines():
                f.write(line + "\n")
    
    print(f"✓ Created reference genome: {fasta_path}")
    print(f"✓ Created annotation: {gtf_path}")
    print(f"  - {len(genes)} genes")
    print(f"  - {len(CHROMOSOMES)} chromosomes")
    print(f"  - ~{sum(len(g.sequence) for g in genes) / 1000:.1f}kb total")
    
    return fasta_path, gtf_path

def generate_reads_from_gene(gene, num_reads, condition='control'):
    """Generate RNA-seq reads from a gene."""
    reads = []
    exon_seq = gene.get_exon_sequence()
    
    if len(exon_seq) < 2 * READ_LENGTH:
        return []  # Gene too short
    
    for _ in range(num_reads):
        # Random fragment start position
        max_start = len(exon_seq) - 2 * READ_LENGTH
        if max_start <= 0:
            continue
        
        frag_start = random.randint(0, max_start)
        
        # Extract paired-end reads
        if gene.strand == '+':
            # Forward strand
            read1 = exon_seq[frag_start:frag_start + READ_LENGTH]
            read2 = reverse_complement(exon_seq[frag_start + READ_LENGTH:frag_start + 2 * READ_LENGTH])
        else:
            # Reverse strand
            read1 = reverse_complement(exon_seq[frag_start + READ_LENGTH:frag_start + 2 * READ_LENGTH])
            read2 = exon_seq[frag_start:frag_start + READ_LENGTH]
        
        # Add sequencing errors
        read1 = mutate_sequence(read1, error_rate=0.005)
        read2 = mutate_sequence(read2, error_rate=0.005)
        
        reads.append((read1, read2))
    
    return reads

def generate_sample(genes, sample_name, output_dir, expression_profile):
    """Generate a complete RNA-seq sample."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_reads_r1 = []
    all_reads_r2 = []
    
    for gene in genes:
        # Get expression level for this gene
        base_expression = expression_profile.get(gene.gene_id, 1.0)
        
        # Add biological variation
        expression = base_expression * random.uniform(0.8, 1.2)
        
        # Convert expression to read count (proportional)
        num_reads = int(READS_PER_SAMPLE * expression / sum(expression_profile.values()))
        
        # Generate reads
        reads = generate_reads_from_gene(gene, num_reads)
        for r1, r2 in reads:
            all_reads_r1.append(r1)
            all_reads_r2.append(r2)
    
    # Shuffle reads (simulate random sequencing)
    combined = list(zip(all_reads_r1, all_reads_r2))
    random.shuffle(combined)
    all_reads_r1, all_reads_r2 = zip(*combined) if combined else ([], [])
    
    # Write FASTQ files (gzipped)
    fq1_path = output_dir / f"{sample_name}_1.fq.gz"
    fq2_path = output_dir / f"{sample_name}_2.fq.gz"
    
    with gzip.open(fq1_path, 'wt') as f1, gzip.open(fq2_path, 'wt') as f2:
        for i, (r1, r2) in enumerate(zip(all_reads_r1, all_reads_r2), 1):
            # Write R1
            f1.write(f"@{sample_name}_{i}/1\n")
            f1.write(f"{r1}\n")
            f1.write("+\n")
            f1.write(f"{quality_string(len(r1))}\n")
            
            # Write R2
            f2.write(f"@{sample_name}_{i}/2\n")
            f2.write(f"{r2}\n")
            f2.write("+\n")
            f2.write(f"{quality_string(len(r2))}\n")
    
    print(f"✓ Generated {sample_name}: {len(all_reads_r1)} read pairs")
    return fq1_path, fq2_path

def main():
    """Main function to generate demo data."""
    print("=" * 60)
    print("ExpressDiff Demo Data Generator")
    print("=" * 60)
    print()
    
    # Create genes
    print("Step 1: Creating gene structures...")
    genes = []
    gene_pos = 5000  # Start position on chromosome
    
    for i in range(NUM_GENES):
        chrom = CHROMOSOMES[i % len(CHROMOSOMES)]
        strand = random.choice(['+', '-'])
        gene_id = f"DEMO{i+1:04d}"
        
        gene = Gene(gene_id, chrom, gene_pos, strand)
        genes.append(gene)
        
        # Move to next gene position (add some intergenic space)
        gene_pos = gene.end + random.randint(500, 2000)
        
        # Reset position for next chromosome
        if (i + 1) % (NUM_GENES // len(CHROMOSOMES)) == 0:
            gene_pos = 5000
    
    print(f"✓ Created {NUM_GENES} genes")
    print()
    
    # Generate reference genome
    print("Step 2: Generating reference genome...")
    ref_dir = Path("demo_reference")
    fasta_path, gtf_path = generate_reference_genome(genes, ref_dir)
    print()
    
    # Create expression profiles
    print("Step 3: Designing expression profiles...")
    
    # Base expression (all genes expressed at some level)
    base_expression = {gene.gene_id: random.uniform(0.5, 2.0) for gene in genes}
    
    # Control samples - use base expression
    control_expression = base_expression.copy()
    
    # Treatment samples - modify expression for some genes
    treatment_expression = base_expression.copy()
    
    # Upregulate 10 genes (2-fold)
    upregulated = random.sample(genes[:50], 10)
    for gene in upregulated:
        treatment_expression[gene.gene_id] *= 2.0
    
    # Downregulate 10 genes (0.5-fold)
    downregulated = random.sample(genes[50:], 10)
    for gene in downregulated:
        treatment_expression[gene.gene_id] *= 0.5
    
    print(f"✓ Control expression: {NUM_GENES} genes")
    print(f"✓ Treatment expression: {NUM_GENES} genes")
    print(f"  - {len(upregulated)} upregulated (2x)")
    print(f"  - {len(downregulated)} downregulated (0.5x)")
    print()
    
    # Generate samples
    print("Step 4: Generating RNA-seq samples...")
    demo_dir = Path("demo_data")
    
    # Control samples
    for i in range(NUM_REPLICATES):
        sample_name = f"control_{i+1}"
        generate_sample(genes, sample_name, demo_dir, control_expression)
    
    # Treatment samples
    for i in range(NUM_REPLICATES):
        sample_name = f"treatment_{i+1}"
        generate_sample(genes, sample_name, demo_dir, treatment_expression)
    
    print()
    print("=" * 60)
    print("✓ Demo data generation complete!")
    print("=" * 60)
    print()
    print("Output files:")
    print(f"  Reference: {ref_dir}/")
    print(f"    - demo_genome.fa")
    print(f"    - demo_annotation.gtf")
    print(f"  Samples: {demo_dir}/")
    print(f"    - control_1_1.fq.gz, control_1_2.fq.gz")
    print(f"    - control_2_1.fq.gz, control_2_2.fq.gz")
    print(f"    - control_3_1.fq.gz, control_3_2.fq.gz")
    print(f"    - treatment_1_1.fq.gz, treatment_1_2.fq.gz")
    print(f"    - treatment_2_1.fq.gz, treatment_2_2.fq.gz")
    print(f"    - treatment_3_1.fq.gz, treatment_3_2.fq.gz")
    print()
    print("Expected pipeline runtime: ~5-10 minutes")
    print("Expected differential expression: ~20 genes (10 up, 10 down)")
    print()
    print("To use this data:")
    print("  1. Upload the 6 FASTQ files (3 control + 3 treatment)")
    print("  2. Upload demo_genome.fa and demo_annotation.gtf as reference")
    print("  3. Run the full pipeline")
    print("  4. Expect ~40-50% alignment rate")
    print("  5. DESeq2 should detect ~20 differentially expressed genes")

if __name__ == "__main__":
    main()
