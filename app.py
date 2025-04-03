# app.py
import streamlit as st
import pandas as pd
import sqlite3
import tempfile
from utils.query_utils import generate_sql, run_sql

st.set_page_config(page_title="GenAI SQL Assistant", layout="wide")

st.title("🧠 GenAI SQL Assistant")
st.write("Upload your Excel or CSV file and ask questions in plain English.")

uploaded_file = st.file_uploader("📤 Upload a CSV or Excel file", type=["csv", "xlsx"])

df = None
conn = None

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("✅ File uploaded successfully!")
        st.write("Preview of uploaded data:")
        st.dataframe(df)

        # Create temp SQLite DB and load data
        conn = sqlite3.connect(":memory:")
        df.to_sql("uploaded_data", conn, index=False, if_exists="replace")

        # Prompt box
        user_input = st.text_input("🔍 Ask your question (e.g., 'Show me average sales by region')")

        if user_input:
            with st.spinner("Generating SQL..."):
                # Dynamically build schema string for prompt context
                schema_info = f"CREATE TABLE uploaded_data ({', '.join(f'{col} {pd.api.types.infer_dtype(df[col])}' for col in df.columns)});"

                sql = generate_sql(user_input, schema_info)
                st.code(sql, language="sql")

                try:
                    result = run_sql(conn, sql)
                    st.success("✅ Query executed successfully!")
                    st.dataframe(result)

                    if result.shape[1] >= 2:
                        try:
                            st.bar_chart(result.set_index(result.columns[0]))
                        except Exception as e:
                            st.warning(f"⚠️ Chart rendering skipped due to error: {e}")
                except Exception as e:
                    st.error(f"❌ Failed to run SQL: {e}")

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
