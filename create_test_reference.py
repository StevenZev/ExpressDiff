#!/usr/bin/env python3
"""
Generate minimal test reference genome and annotation files for ExpressDiff testing.
Creates tiny FASTA and GTF files that work with STAR but index quickly.
"""
import gzip
from pathlib import Path

def create_test_fasta(output_file, num_chroms=3, chrom_length=10000):
    """Create a minimal reference genome FASTA file."""
    print(f"Creating test FASTA: {output_file}")
    
    bases = "ATCG"
    with open(output_file, 'w') as f:
        for chrom_num in range(1, num_chroms + 1):
            chrom_name = f"chr{chrom_num}"
            f.write(f">{chrom_name}\n")
            
            # Write sequence in 60-character lines (FASTA standard)
            for pos in range(0, chrom_length, 60):
                # Create semi-random but reproducible sequence
                line_length = min(60, chrom_length - pos)
                sequence = ''.join([bases[(pos + i + chrom_num) % 4] for i in range(line_length)])
                f.write(sequence + '\n')
    
    print(f"  Created {num_chroms} chromosomes, {chrom_length}bp each")
    print(f"  Total size: {Path(output_file).stat().st_size:,} bytes")


def create_test_gtf(output_file, num_chroms=3, genes_per_chrom=10):
    """Create a minimal GTF annotation file."""
    print(f"\nCreating test GTF: {output_file}")
    
    with open(output_file, 'w') as f:
        # GTF header
        f.write("##description: Minimal test annotation for ExpressDiff testing\n")
        f.write("##provider: ExpressDiff\n")
        f.write("##format: gtf\n")
        f.write("##date: 2025-10-07\n")
        
        gene_id_counter = 1
        
        for chrom_num in range(1, num_chroms + 1):
            chrom_name = f"chr{chrom_num}"
            
            for gene_num in range(genes_per_chrom):
                gene_id = f"GENE{gene_id_counter:04d}"
                gene_name = f"TestGene{gene_id_counter}"
                transcript_id = f"{gene_id}.1"
                
                # Gene coordinates (non-overlapping)
                gene_start = gene_num * 900 + 100
                gene_end = gene_start + 800
                
                # Strand (alternate between + and -)
                strand = "+" if gene_num % 2 == 0 else "-"
                
                # Gene feature
                f.write(f"{chrom_name}\ttest\tgene\t{gene_start}\t{gene_end}\t.\t{strand}\t.\t"
                       f'gene_id "{gene_id}"; gene_type "protein_coding"; gene_name "{gene_name}";\n')
                
                # Transcript feature
                f.write(f"{chrom_name}\ttest\ttranscript\t{gene_start}\t{gene_end}\t.\t{strand}\t.\t"
                       f'gene_id "{gene_id}"; transcript_id "{transcript_id}"; gene_name "{gene_name}";\n')
                
                # Exon 1
                exon1_start = gene_start
                exon1_end = gene_start + 300
                f.write(f"{chrom_name}\ttest\texon\t{exon1_start}\t{exon1_end}\t.\t{strand}\t.\t"
                       f'gene_id "{gene_id}"; transcript_id "{transcript_id}"; exon_number "1"; gene_name "{gene_name}";\n')
                
                # Exon 2
                exon2_start = gene_end - 300
                exon2_end = gene_end
                f.write(f"{chrom_name}\ttest\texon\t{exon2_start}\t{exon2_end}\t.\t{strand}\t.\t"
                       f'gene_id "{gene_id}"; transcript_id "{transcript_id}"; exon_number "2"; gene_name "{gene_name}";\n')
                
                gene_id_counter += 1
    
    total_genes = (num_chroms * genes_per_chrom)
    print(f"  Created {total_genes} genes ({genes_per_chrom} per chromosome)")
    print(f"  Total size: {Path(output_file).stat().st_size:,} bytes")


def main():
    """Generate test reference files in test_data directory."""
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Test Reference Genome Files")
    print("=" * 60)
    
    # Create minimal reference files
    # Small enough to index quickly (~1-2 minutes) but realistic structure
    fasta_file = test_data_dir / "test_genome.fa"
    gtf_file = test_data_dir / "test_annotation.gtf"
    
    create_test_fasta(
        fasta_file,
        num_chroms=3,      # 3 chromosomes
        chrom_length=10000 # 10kb each = 30kb total (vs 2.6GB real genome!)
    )
    
    create_test_gtf(
        gtf_file,
        num_chroms=3,
        genes_per_chrom=10  # 30 total genes (vs 50,000+ in real genome!)
    )
    
    print("\n" + "=" * 60)
    print("✅ Test reference files created!")
    print("=" * 60)
    print(f"\nFiles created in: {test_data_dir}")
    print(f"  • {fasta_file.name}")
    print(f"  • {gtf_file.name}")
    
    print("\n💡 Usage:")
    print(f"  1. Copy to run-specific reference directory:")
    print(f"     cp {test_data_dir}/test_* /scratch/vth3bk/ExpressDiff/runs/{{RUN_ID}}/reference/")
    print(f"  2. Or use as global test reference:")
    print(f"     cp {test_data_dir}/test_* /home/vth3bk/Pipelinin/ExpressDiff/mapping_in/")
    print(f"\n⚡ Benefits:")
    print(f"  • STAR index: ~5 seconds (vs 25 minutes)")
    print(f"  • Alignment: ~10 seconds (vs 5 minutes)")
    print(f"  • Disk: <1 MB (vs 10+ GB)")
    
    # Show file contents preview
    print("\n" + "=" * 60)
    print("File Previews:")
    print("=" * 60)
    
    print("\n📄 FASTA (first 10 lines):")
    with open(fasta_file) as f:
        for i, line in enumerate(f):
            if i >= 10:
                break
            print(f"  {line.rstrip()}")
    
    print("\n📄 GTF (first 10 lines):")
    with open(gtf_file) as f:
        for i, line in enumerate(f):
            if i >= 10:
                break
            print(f"  {line.rstrip()}")


if __name__ == "__main__":
    main()
