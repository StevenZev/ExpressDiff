# Testing & Smoke Checks

ExpressDiff does not currently ship with a formal automated test suite; verification is typically done via a small end-to-end “smoke run”.

## Generate Small Test Inputs

Use the built-in generators in `ExpressDiff/test_data_generators/README.md:1`:
```bash
cd ExpressDiff/test_data_generators
./create_test_data.sh
python create_test_reference.py
./create_demo_metadata.sh
```

Outputs land in `ExpressDiff/test_data/`.

## Use the Bundled Demo Dataset

If you just want a ready-to-upload set of reads + reference + metadata, use:
- `ExpressDiff/docs/DEMO_DATASET.md:1`

## Backend Smoke Check (No SLURM)

```bash
cd ExpressDiff
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

Then:
- `GET /health`
- `GET /stages`
- `POST /runs`

Endpoints are defined in `ExpressDiff/backend/api/main.py:1`.

## End-to-End Smoke Check (HPC + SLURM)

1. Start ExpressDiff via module launcher (`ExpressDiff/bin/ExpressDiff:1`).
2. Create a run in the UI.
3. Upload:
   - paired FASTQ (`*.fq.gz`)
   - reference FASTA (`*.fa`) and GTF (`*.gtf`)
   - metadata CSV for DE stage (`metadata.csv`)
4. Execute stages in order (see `ExpressDiff/docs/PIPELINE.md:1`).
5. Confirm “done flags” appear under the run directory and results endpoints load.
