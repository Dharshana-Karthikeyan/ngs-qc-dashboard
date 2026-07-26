#!/usr/bin/env python3
import sys
import json
import glob
import sqlite3
import argparse


def derive_overall_status(module_verdicts: dict) -> str:
    verdicts = [v.lower() for v in module_verdicts.values()]
    if "fail" in verdicts:
        return "FAIL"
    if "warn" in verdicts:
        return "WARN"
    return "PASS"


def init_db(conn: sqlite3.Connection, schema_path: str = "schema.sql"):
    with open(schema_path, "r") as f:
        conn.executescript(f.read())
    conn.commit()


def ingest_file(conn: sqlite3.Connection, json_path: str):
    with open(json_path, "r") as f:
        metrics = json.load(f)

    overall_status = derive_overall_status(metrics["module_verdicts"])

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO samples (
            sample_name, total_reads, sequence_length, gc_content_pct,
            avg_quality_score, duplication_rate_pct,
            max_adapter_contamination_pct, overall_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sample_name) DO UPDATE SET
            total_reads=excluded.total_reads,
            sequence_length=excluded.sequence_length,
            gc_content_pct=excluded.gc_content_pct,
            avg_quality_score=excluded.avg_quality_score,
            duplication_rate_pct=excluded.duplication_rate_pct,
            max_adapter_contamination_pct=excluded.max_adapter_contamination_pct,
            overall_status=excluded.overall_status
    """, (
        metrics["sample_name"],
        metrics["total_reads"],
        metrics["sequence_length"],
        metrics["gc_content_pct"],
        metrics["avg_quality_score"],
        metrics["duplication_rate_pct"],
        metrics["max_adapter_contamination_pct"],
        overall_status,
    ))

    cur.execute("SELECT id FROM samples WHERE sample_name = ?", (metrics["sample_name"],))
    sample_id = cur.fetchone()[0]

    cur.execute("DELETE FROM module_verdicts WHERE sample_id = ?", (sample_id,))
    for module, verdict in metrics["module_verdicts"].items():
        cur.execute(
            "INSERT INTO module_verdicts (sample_id, module_name, verdict) VALUES (?, ?, ?)",
            (sample_id, module, verdict)
        )

    conn.commit()
    print(f"Ingested: {metrics['sample_name']} -> overall status: {overall_status}")


def main():
    parser = argparse.ArgumentParser(description="Ingest FastQC JSON metrics into SQLite.")
    parser.add_argument("json_files", nargs="+", help="JSON file(s) to ingest (globs OK)")
    parser.add_argument("--db", default="qc_dashboard.db", help="Path to SQLite DB file")
    parser.add_argument("--schema", default="schema.sql", help="Path to schema.sql")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn, args.schema)

    files = []
    for pattern in args.json_files:
        files.extend(glob.glob(pattern))

    if not files:
        print("No JSON files matched.")
        sys.exit(1)

    for path in files:
        ingest_file(conn, path)

    conn.close()
    print(f"\nDone. Database: {args.db}")


if __name__ == "__main__":
    main()
