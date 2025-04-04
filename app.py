# app.py
import streamlit as st
import pandas as pd
import sqlite3
import os
import tempfile

from utils.query_utils import get_schema, generate_sql, run_sql

st.set_page_config(page_title="GenAI SQL Assistant", layout="wide")
st.title("🤖 GenAI SQL Assistant")

uploaded_file = st.file_uploader("📁 Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    # Save uploaded file to a temp directory
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(tmp_path)
    else:
        df = pd.read_excel(tmp_path)

    st.success("✅ File uploaded successfully")
    st.write("Preview:")
    st.dataframe(df)

    # Save to SQLite
    conn = sqlite3.connect("uploaded_data.db")
    table_name = "uploaded_data"
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

    user_input = st.text_input("🔍 Ask your question (e.g., 'Show average sales by region')")

    if user_input:
        with st.spinner("Generating SQL..."):
            schema = get_schema("uploaded_data.db")
            sql = generate_sql(user_input, schema)
            st.code(sql, language="sql")

        try:
            result = run_sql("uploaded_data.db", sql)
            if result.empty:
                st.warning("⚠️ Query executed successfully, but returned no results.")
            else:
                st.dataframe(result)
                if result.shape[1] >= 2:
                    st.bar_chart(result.set_index(result.columns[0]))
        except Exception as e:
            st.error(f"❌ Failed to run SQL: {e}")