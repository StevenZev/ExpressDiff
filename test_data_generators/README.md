# Test Data Generators

This directory contains scripts for generating test and demo data for ExpressDiff.

## Scripts

### `create_test_data.sh`
**Purpose**: Generate small FASTQ test files for basic testing

**Usage**:
```bash
./create_test_data.sh
```

**Generates**:
- Small paired-end FASTQ files in `../test_data/`
- Suitable for quick functionality tests
- Files: sample_A_1.fq.gz, sample_A_2.fq.gz, etc.

---

### `create_test_reference.py`
**Purpose**: Generate minimal reference genome and GTF annotation files

**Usage**:
```bash
python create_test_reference.py
```

**Generates**:
- `../test_data/test_genome.fa` - Small test genome (3 chromosomes)
- `../test_data/test_annotation.gtf` - Minimal GTF with gene annotations
- Suitable for testing alignment and quantification without downloading large references

---

### `create_demo_data.py`
**Purpose**: Generate demo FASTQ files with realistic characteristics

**Usage**:
```bash
python create_demo_data.py
```

**Generates**:
- Demo FASTQ files with controlled read counts
- Simulates differential expression between conditions
- Good for demonstration purposes

---

### `create_demo_metadata.sh`
**Purpose**: Generate demo metadata CSV file

**Usage**:
```bash
./create_demo_metadata.sh
```

**Generates**:
- Metadata CSV file for demo samples
- Includes sample names, conditions, and other experimental metadata

---

### `create_valid_test_data.py`
**Purpose**: Generate valid test data for validation testing

**Usage**:
```bash
python create_valid_test_data.py
```

**Generates**:
- Test data with specific validation scenarios
- Used for testing the validation system

---

## Quick Start

To set up a complete test environment:

```bash
cd test_data_generators

# 1. Generate test FASTQ files
./create_test_data.sh

# 2. Generate reference genome and GTF
python create_test_reference.py

# 3. (Optional) Generate demo data
python create_demo_data.py
./create_demo_metadata.sh
```

After running these scripts, you'll have everything needed to test the ExpressDiff pipeline.

## Output Directory

All scripts output to the `../test_data/` directory by default. This keeps generated test files separate from the generator scripts.

## Requirements

- **Bash** - For shell scripts (.sh)
- **Python 3.6+** - For Python scripts (.py)
- No additional Python packages required (uses standard library only)

## Notes

- These scripts generate **small test files** suitable for development and testing
- For production use, users should provide real reference genomes and experimental data
- Test files are intentionally minimal to enable fast testing cycles
- All scripts are self-contained and don't require external data

## Support

For questions about test data generation, contact: vth3bk@virginia.edu
