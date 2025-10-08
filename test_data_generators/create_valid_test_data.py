#!/usr/bin/env python3
"""
Generate valid paired-end FASTQ test data for ExpressDiff pipeline testing.
Creates properly formatted gzipped FASTQ files with matching sequence/quality lengths.
"""
import gzip
import random
from pathlib import Path

def generate_random_sequence(length=75):
    """Generate a random DNA sequence."""
    return ''.join(random.choices('ATCG', k=length))

def generate_quality_scores(length=75):
    """Generate quality scores (Phred+33 format)."""
    # Use realistic Illumina quality score range (Phred+33: ! = Q0, ~ = Q93)
    # Typical range: # (Q2) to I (Q40), with most being high quality
    # This gives Trimmomatic enough variation to detect Phred+33 encoding
    quality_chars = '##$$%%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIIIIIIIIIIIIII'
    return ''.join(random.choices(quality_chars, k=length))

def create_fastq_record(seq_id, sequence, is_reverse=False):
    """Create a single FASTQ record."""
    quality = generate_quality_scores(len(sequence))
    direction = "reverse" if is_reverse else "forward"
    return f"@SEQ_{seq_id}_{direction}\n{sequence}\n+\n{quality}\n"

def create_paired_fastq_files(sample_name, output_dir, num_reads=1000, read_length=75):
    """Create paired-end FASTQ files for a sample."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fwd_file = output_dir / f"{sample_name}_1.fq.gz"
    rev_file = output_dir / f"{sample_name}_2.fq.gz"
    
    print(f"Creating {sample_name} with {num_reads} read pairs...")
    
    with gzip.open(fwd_file, 'wt') as fwd, gzip.open(rev_file, 'wt') as rev:
        for i in range(1, num_reads + 1):
            # Generate paired sequences
            fwd_seq = generate_random_sequence(read_length)
            rev_seq = generate_random_sequence(read_length)
            
            # Write FASTQ records
            fwd.write(create_fastq_record(i, fwd_seq, is_reverse=False))
            rev.write(create_fastq_record(i, rev_seq, is_reverse=True))
    
    print(f"  Created: {fwd_file} ({fwd_file.stat().st_size} bytes)")
    print(f"  Created: {rev_file} ({rev_file.stat().st_size} bytes)")

def main():
    """Generate test data for three samples."""
    test_data_dir = Path(__file__).parent / "test_data"
    
    # Remove old test data
    if test_data_dir.exists():
        print("Removing old test data...")
        for f in test_data_dir.glob("*.fq.gz"):
            f.unlink()
        for f in test_data_dir.glob("*.fq"):
            f.unlink()
    
    # Create new valid test data
    print("\nGenerating valid test FASTQ files...")
    print("=" * 50)
    
    samples = ["sample_A", "sample_B", "sample_C"]
    for sample in samples:
        create_paired_fastq_files(sample, test_data_dir, num_reads=1000, read_length=75)
    
    print("=" * 50)
    print("\nTest data generation complete!")
    print(f"Files created in: {test_data_dir}")
    print("\nYou can now upload these files to test the pipeline.")

if __name__ == "__main__":
    random.seed(42)  # Reproducible test data
    main()
