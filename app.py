# app.py
import streamlit as st
import pandas as pd
import os

from utils.query_utils import get_schema, generate_sql, run_sql

st.set_page_config(page_title="GenAI SQL Assistant", layout="wide")

st.title("🤖 GenAI SQL Assistant")

uploaded_file = st.file_uploader("📁 Upload a CSV or Excel file", type=["csv", "xlsx"])

df = None
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("✅ File uploaded successfully")
        st.write("Preview:")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error loading file: {e}")

user_input = st.text_input("💬 Ask a question about your data")

if user_input:
    with st.spinner("Generating SQL..."):
        try:
            schema = get_schema()
            sql = generate_sql(user_input, schema)
            st.code(sql, language="sql")

            result = run_sql(sql, df)
            if result.empty:
                st.warning("⚠️ No results returned.")
            else:
                st.dataframe(result)

                # Render chart only if numeric columns exist
                numeric_cols = result.select_dtypes(include='number').columns
                if len(numeric_cols) >= 1:
                    st.bar_chart(result[numeric_cols])
        except Exception as e:
            st.error(f"Error: {e}")
