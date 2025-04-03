# app.py

import streamlit as st
from utils.query_utils import get_schema, generate_sql, run_sql
import pandas as pd

st.set_page_config(page_title="GenAI SQL Assistant", layout="wide")

# Title
st.title("🧠 GenAI SQL Assistant")
st.write("Ask a question about your database in natural language:")

# Input box
user_input = st.text_input("💬 Your question", placeholder="e.g. Show top 5 products by revenue")

if user_input:
    with st.spinner("Generating SQL..."):
        schema = get_schema()
        sql = generate_sql(user_input, schema)

        st.subheader("🧾 Generated SQL")
        st.code(sql, language="sql")

        result = run_sql(sql)

    if isinstance(result, str):
        st.error(result)
    else:
        st.success("✅ Query successful")
        st.subheader("📊 Results")
        st.dataframe(result)

        # Optional chart (if valid)
        try:
            if result.shape[1] >= 2:
                st.bar_chart(result.set_index(result.columns[0]))
        except Exception as e:
            st.warning(f"⚠️ Could not render chart: {e}")

        # CSV download
        csv = result.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download CSV", csv, "query_results.csv", "text/csv")
