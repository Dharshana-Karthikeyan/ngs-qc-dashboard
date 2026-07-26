#!/usr/bin/env python3
"""
FastQC Parser
-------------
Parses a FastQC `fastqc_data.txt` file and extracts standardized QC metrics:
    - sample name
    - total reads
    - %GC content
    - average per-base read quality
    - duplication rate
    - max adapter contamination %
    - PASS/WARN/FAIL verdict per FastQC module

Usage:
    python3 parser.py <path_to_fastqc_data.txt> [--json output.json]
"""

import sys
import json
import argparse
from pathlib import Path


def parse_fastqc_data(filepath: str) -> dict:
    """Parse a fastqc_data.txt file and return a dict of standardized metrics."""

    with open(filepath, "r") as f:
        lines = f.readlines()

    # Split file into sections keyed by module name.
    # Each section starts with a line like ">>Module Name<TAB>verdict"
    # and ends with ">>END_MODULE"
    sections = {}
    current_module = None
    current_lines = []
    module_verdicts = {}

    for line in lines:
        line = line.rstrip("\n")

        if line.startswith(">>") and not line.startswith(">>END_MODULE"):
            # New module header, e.g. ">>Basic Statistics\tpass"
            parts = line[2:].split("\t")
            module_name = parts[0]
            verdict = parts[1] if len(parts) > 1 else None
            current_module = module_name
            current_lines = []
            module_verdicts[module_name] = verdict

        elif line.startswith(">>END_MODULE"):
            if current_module is not None:
                sections[current_module] = current_lines
            current_module = None
            current_lines = []

        elif current_module is not None:
            current_lines.append(line)

    # ---- Extract Basic Statistics ----
    basic_stats = {}
    for row in sections.get("Basic Statistics", []):
        if row.startswith("#"):
            continue
        if "\t" in row:
            key, value = row.split("\t", 1)
            basic_stats[key] = value

    sample_name = basic_stats.get("Filename", Path(filepath).stem)
    total_reads = int(basic_stats.get("Total Sequences", 0))
    gc_content = float(basic_stats.get("%GC", 0))
    sequence_length = basic_stats.get("Sequence length", "NA")

    # ---- Extract average per-base quality ----
    # "Per base sequence quality" table columns: Base  Mean  Median  ...
    quality_rows = sections.get("Per base sequence quality", [])
    means = []
    for row in quality_rows:
        if row.startswith("#"):
            continue
        cols = row.split("\t")
        if len(cols) >= 2:
            try:
                means.append(float(cols[1]))
            except ValueError:
                continue
    avg_quality = round(sum(means) / len(means), 2) if means else None

    # ---- Extract duplication rate ----
    dup_rows = sections.get("Sequence Duplication Levels", [])
    dedup_percentage = None
    for row in dup_rows:
        if row.startswith("#Total Deduplicated Percentage"):
            dedup_percentage = float(row.split("\t")[1])
            break
    duplication_rate = round(100 - dedup_percentage, 2) if dedup_percentage is not None else None

    # ---- Extract max adapter contamination ----
    adapter_rows = sections.get("Adapter Content", [])
    max_adapter_pct = 0.0
    for row in adapter_rows:
        if row.startswith("#"):
            continue
        cols = row.split("\t")
        if len(cols) > 1:
            values = [float(v) for v in cols[1:] if v.replace(".", "", 1).isdigit()]
            if values:
                max_adapter_pct = max(max_adapter_pct, max(values))

    # ---- Build final result ----
    result = {
        "sample_name": sample_name,
        "total_reads": total_reads,
        "sequence_length": sequence_length,
        "gc_content_pct": gc_content,
        "avg_quality_score": avg_quality,
        "duplication_rate_pct": duplication_rate,
        "max_adapter_contamination_pct": round(max_adapter_pct, 3),
        "module_verdicts": module_verdicts,
    }

    return result


def print_summary(metrics: dict) -> None:
    """Pretty-print the extracted metrics to console."""
    print("=" * 55)
    print(f"Sample: {metrics['sample_name']}")
    print("=" * 55)
    print(f"Total reads:                {metrics['total_reads']:,}")
    print(f"Sequence length range:      {metrics['sequence_length']}")
    print(f"GC content:                 {metrics['gc_content_pct']}%")
    print(f"Avg per-base quality score: {metrics['avg_quality_score']}")
    print(f"Duplication rate:           {metrics['duplication_rate_pct']}%")
    print(f"Max adapter contamination:  {metrics['max_adapter_contamination_pct']}%")
    print("-" * 55)
    print("Module verdicts:")
    for module, verdict in metrics["module_verdicts"].items():
        print(f"  [{verdict.upper():4}] {module}")
    print("=" * 55)


def main():
    parser = argparse.ArgumentParser(description="Parse a FastQC fastqc_data.txt file.")
    parser.add_argument("input", help="Path to fastqc_data.txt")
    parser.add_argument("--json", help="Optional path to save output as JSON", default=None)
    args = parser.parse_args()

    metrics = parse_fastqc_data(args.input)
    print_summary(metrics)

    if args.json:
        with open(args.json, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"\nSaved JSON output to: {args.json}")


if __name__ == "__main__":
    main()