# app.py
import streamlit as st
import pandas as pd
import sqlite3
import os
from utils.query_utils import get_schema, generate_sql, run_sql

st.set_page_config(page_title="GenAI SQL Assistant", layout="wide")
st.title("🧠 GenAI SQL Assistant")

uploaded_file = st.file_uploader("📂 Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        try:
            df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"❌ Failed to read Excel file: {e}")
            st.stop()

    st.success("✅ File uploaded successfully")
    st.write("Preview:")
    st.dataframe(df)

    # Save uploaded data to SQLite database
    os.makedirs("schema", exist_ok=True)
    conn = sqlite3.connect("schema/sample_data.db")

    table_name = os.path.splitext(uploaded_file.name)[0].replace(" ", "_")
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

    st.success(f"✅ Data written to SQLite as table: `{table_name}`")

    user_input = st.text_input("🔍 Ask your question (e.g., 'Show average sales by genre')")

    if user_input:
        with st.spinner("Generating SQL..."):
            schema = get_schema()
            sql = generate_sql(user_input, schema)
            st.code(sql, language='sql')

            try:
                result = run_sql(sql)
                if result.empty:
                    st.warning("⚠️ Query returned no results.")
                else:
                    st.dataframe(result)
                    if result.shape[1] >= 2:
                        try:
                            st.bar_chart(result.set_index(result.columns[0]))
                        except Exception as e:
                            st.warning(f"⚠️ Chart rendering failed: {e}")
            except Exception as e:
                st.error(f"❌ Failed to run SQL: {e}")
