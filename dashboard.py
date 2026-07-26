#!/usr/bin/env python3
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = "qc_dashboard.db"

st.set_page_config(page_title="NGS QC Dashboard", layout="wide")
st.title("🧬 NGS QC Dashboard")
st.caption("Batch quality-control overview across sequencing samples (FastQC-derived metrics)")


@st.cache_data(ttl=5)
def load_samples():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM samples ORDER BY sample_name", conn)
    conn.close()
    return df


@st.cache_data(ttl=5)
def load_module_verdicts():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT s.sample_name, m.module_name, m.verdict
        FROM module_verdicts m
        JOIN samples s ON s.id = m.sample_id
    """, conn)
    conn.close()
    return df


try:
    samples_df = load_samples()
except Exception as e:
    st.error(f"Could not load database at '{DB_PATH}'. Have you run ingest.py yet? ({e})")
    st.stop()

if samples_df.empty:
    st.warning("No samples found in the database yet. Run ingest.py to load some.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total samples", len(samples_df))
col2.metric("PASS", int((samples_df["overall_status"] == "PASS").sum()))
col3.metric("WARN", int((samples_df["overall_status"] == "WARN").sum()))
col4.metric("FAIL", int((samples_df["overall_status"] == "FAIL").sum()))

st.divider()

status_filter = st.multiselect(
    "Filter by overall status",
    options=["PASS", "WARN", "FAIL"],
    default=["PASS", "WARN", "FAIL"],
)
filtered = samples_df[samples_df["overall_status"].isin(status_filter)]


def highlight_status(row):
    color = {"PASS": "#d4edda", "WARN": "#fff3cd", "FAIL": "#f8d7da"}.get(row["overall_status"], "")
    return [f"background-color: {color}"] * len(row)


st.subheader("Sample overview")
st.dataframe(
    filtered[[
        "sample_name", "overall_status", "total_reads", "gc_content_pct",
        "avg_quality_score", "duplication_rate_pct", "max_adapter_contamination_pct"
    ]].style.apply(highlight_status, axis=1),
    use_container_width=True,
)

st.divider()

c1, c2 = st.columns(2)
with c1:
    st.subheader("Average quality score by sample")
    st.bar_chart(filtered.set_index("sample_name")["avg_quality_score"])
with c2:
    st.subheader("GC content by sample")
    st.bar_chart(filtered.set_index("sample_name")["gc_content_pct"])

st.divider()

st.subheader("Per-module verdicts")
verdicts_df = load_module_verdicts()
if not verdicts_df.empty:
    pivot = verdicts_df.pivot(index="sample_name", columns="module_name", values="verdict")
    st.dataframe(pivot, use_container_width=True)
