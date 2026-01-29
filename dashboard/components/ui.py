"""
dashboard/components/ui.py

Helper visualization utilities (starter file).
"""
from __future__ import annotations
import streamlit as st
import pandas as pd


def show_dataframe(df: pd.DataFrame, max_rows: int = 100):
    st.dataframe(df.head(max_rows))
