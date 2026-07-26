-- NGS QC Dashboard database schema (SQLite)

CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_name TEXT NOT NULL UNIQUE,
    total_reads INTEGER,
    sequence_length TEXT,
    gc_content_pct REAL,
    avg_quality_score REAL,
    duplication_rate_pct REAL,
    max_adapter_contamination_pct REAL,
    overall_status TEXT,
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS module_verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id INTEGER NOT NULL,
    module_name TEXT NOT NULL,
    verdict TEXT NOT NULL,
    FOREIGN KEY (sample_id) REFERENCES samples(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_module_sample ON module_verdicts(sample_id);
