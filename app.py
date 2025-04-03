# app.py

import streamlit as st
import pandas as pd
import sqlite3
import tempfile

from utils.query_utils import generate_sql, run_sql

st.set_page_config(page_title="GenAI SQL Assistant", layout="wide")
st.title("🧠 GenAI SQL Assistant")

uploaded_file = st.file_uploader("📁 Upload your Excel/CSV file", type=["csv", "xlsx"])

df = None
conn = None

if uploaded_file is not None:
    try:
        # Read and clean the file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Remove unnamed columns (e.g., from blank Excel columns)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.convert_dtypes()

        # Show preview
        st.success("✅ File uploaded successfully")
        st.write("Preview:")
        st.dataframe(df)

        # Save to in-memory SQLite DB
        conn = sqlite3.connect(":memory:")
        df.to_sql("uploaded_data", conn, index=False, if_exists="replace")

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

# User input section
user_input = st.text_input("🔎 Ask your question (e.g., 'Show average sales by genre')")

if user_input and conn:
    with st.spinner("⏳ Generating SQL..."):
        try:
            # Create schema (columns) from uploaded data
            schema = [{"name": col, "type": str(df[col].dtype)} for col in df.columns]
            sql = generate_sql(user_input, schema)
            st.code(sql, language='sql')

            result = run_sql(conn, sql)

            if result.empty:
                st.warning("No results returned.")
            else:
                st.dataframe(result)

                # If suitable, show a chart
                if result.shape[1] >= 2 and pd.api.types.is_numeric_dtype(result.iloc[:, 1]):
                    st.bar_chart(result.set_index(result.columns[0]))

        except Exception as e:
            st.error(f"❌ Failed to run SQL: {e}")
