# NGS QC Dashboard

A lightweight pipeline that parses FastQC quality-control output from DNA sequencing runs, extracts standardized QC metrics, stores them in a SQL database, and visualizes pass/fail status across a batch of samples in an interactive dashboard.

Built as a portfolio project to demonstrate core Linux/NGS bioinformatics workflow skills: environment setup, command-line tools, data parsing, SQL schema design, and lightweight dashboarding.

## What it does

1. Takes FastQC output (`fastqc_data.txt`) from real Illumina sequencing reads
2. Parses out standardized metrics: total reads, GC content, average per-base quality, duplication rate, adapter contamination, and per-module PASS/WARN/FAIL verdicts
3. Loads the parsed metrics into a SQLite database
4. Displays a Streamlit dashboard showing QC status across all ingested samples

## Tech stack

- **Linux (WSL2 / Ubuntu)** — environment
- **FastQC** — sequencing QC tool
- **SRA Toolkit** — public sequencing data retrieval (NCBI SRA)
- **Python 3** — parsing and ingestion scripts
- **SQLite** — metrics storage
- **Streamlit + pandas** — dashboard
- **Docker** — containerization (Dockerfile provided; see note below)

## Pipeline

```
FASTQ (raw reads)
    │
    ▼
FastQC  ──────────► fastqc_data.txt (per-sample QC report)
    │
    ▼
parser.py  ────────► standardized metrics (JSON)
    │
    ▼
ingest.py  ────────► SQLite database (qc_dashboard.db)
    │
    ▼
dashboard.py (Streamlit) ─► visual pass/fail overview
```

## Data used

Sample data: `SRR1030394` (E. coli K-12 MG1655, Illumina paired-end), a small, publicly available bacterial genome sequencing run from NCBI SRA — chosen to keep file sizes and run times small for a portfolio-scale demo. Subset to 50,000 reads per file.

## Setup & usage

```bash
# 1. Clone / enter project directory
cd ngs-qc-dashboard

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run FastQC on your FASTQ files (example)
fastqc your_sample_1.fastq your_sample_2.fastq -o fastqc_output/

# 4. Unzip FastQC results
cd fastqc_output && unzip *_fastqc.zip && cd ..

# 5. Parse metrics from fastqc_data.txt
python3 parser.py fastqc_output/<sample>_fastqc/fastqc_data.txt --json results/<sample>_metrics.json

# 6. Ingest into SQLite
python3 ingest.py results/*.json --db qc_dashboard.db

# 7. Launch dashboard
streamlit run dashboard.py
```

Then open `http://localhost:8501` in your browser.

## Database schema

**`samples`** — one row per sequencing sample, storing extracted metrics and a derived `overall_status` (FAIL if any module fails, WARN if any warns, else PASS).

**`module_verdicts`** — one row per (sample, FastQC module) pair, storing the individual PASS/WARN/FAIL verdict per module (e.g. "Per base sequence quality", "Adapter Content"). Linked to `samples` via foreign key.

This normalization lets the dashboard show both a high-level rollup per sample and a detailed per-module breakdown without duplicating data.

## Docker

A `Dockerfile` is included, based on `python:3.11-slim`, installing dependencies from `requirements.txt` and running the Streamlit app on port 8501. It was **not run in this development environment** (Docker Desktop unavailable), but builds and runs with standard commands:

```bash
docker build -t ngs-qc-dashboard .
docker run -p 8501:8501 ngs-qc-dashboard
```

## Notes on QC results

In the sample data used, **"Per base sequence content"** returns a FastQC `FAIL`, and **GC content** / **sequence length distribution** return `WARN`. These are expected, common results for real shotgun sequencing data (driven by genuine biological signal and natural read-length variability) rather than pipeline errors — and are exactly the kind of nuance a QC dashboard should surface rather than hide.

## Possible extensions

- Support additional QC tools (e.g. MultiQC aggregation)
- Add historical trend tracking across sequencing runs
- Swap SQLite for Postgres for multi-user / production use
- Add automated ingestion via a watched directory or CI pipeline# ngs-qc-dashboard
