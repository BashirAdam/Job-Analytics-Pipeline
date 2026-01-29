"""
dashboard/app.py

Simple Streamlit dashboard that reads from the local DB and provides
interactive filtering and visualizations.

Run locally:
  pip install -r requirements.txt
  streamlit run dashboard/app.py

Expected output: an interactive web UI at http://localhost:8501
"""
from __future__ import annotations
import os
from typing import Optional

import pandas as pd
import streamlit as st
import altair as alt
from sqlalchemy import create_engine

DB_URL_DEFAULT = os.getenv("JOB_PIPELINE_DB_URL", "sqlite:///data/jobs.db")


@st.cache_data
def load_data(db_url: str = DB_URL_DEFAULT) -> pd.DataFrame:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        df = pd.read_sql_table("jobs", conn)
    # Normalize skills into list column for easy explode
    df["skills_list"] = df["skills"].fillna("").apply(lambda s: [i.strip() for i in s.split(",") if i.strip()])
    return df


def show_kpis(df: pd.DataFrame):
    total = len(df)
    companies = df["company_name"].nunique()
    remote_pct = round(100 * df["remote"].mean() if total > 0 else 0, 1)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Jobs", total)
    c2.metric("Unique Companies", companies)
    c3.metric("% Remote", f"{remote_pct}%")


def top_skills_chart(df: pd.DataFrame, top_n: int = 20):
    # Explode skills
    skills_series = df.explode("skills_list")["skills_list"].dropna()
    skills_series = skills_series[skills_series != ""]
    top = skills_series.value_counts().nlargest(top_n).reset_index()
    top.columns = ["skill", "count"]
    chart = alt.Chart(top).mark_bar().encode(
        x=alt.X("count:Q"),
        y=alt.Y("skill:N", sort="-x")
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)


def salary_boxplot(df: pd.DataFrame):
    df_salary = df[df["salary_min"].notnull()]
    if df_salary.empty:
        st.info("No salary data available")
        return
    chart = alt.Chart(df_salary).mark_boxplot().encode(
        x=alt.X("salary_currency:N"),
        y=alt.Y("salary_min:Q")
    )
    st.altair_chart(chart, use_container_width=True)


def main():
    st.set_page_config(page_title="Job Market Analytics", layout="wide")
    st.title("Job Market Analytics Pipeline & Dashboard")

    st.sidebar.header("Data source")
    db_url = st.sidebar.text_input("DB URL", value=DB_URL_DEFAULT)
    st.sidebar.markdown("Run the ETL to populate the DB: `python src/etl_pipeline.py`")

    df = load_data(db_url)

    show_kpis(df)

    st.header("Filters")
    col1, col2 = st.columns(2)
    category = col1.selectbox("Category", options=["All"] + sorted(df["category"].dropna().unique().tolist()))
    company = col2.selectbox("Company", options=["All"] + sorted(df["company_name"].dropna().unique().tolist()))

    filtered = df.copy()
    if category != "All":
        filtered = filtered[filtered["category"] == category]
    if company != "All":
        filtered = filtered[filtered["company_name"] == company]

    st.header("Top Skills")
    top_skills_chart(filtered)

    st.header("Salary overview")
    salary_boxplot(filtered)

    st.header("Recent postings")
    st.dataframe(filtered[["publication_date", "title", "company_name", "location", "skills"]].sort_values(by="publication_date", ascending=False).head(200))


if __name__ == "__main__":
    main()
