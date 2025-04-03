# app.py

import streamlit as st
from utils.query_utils import get_schema, generate_sql, run_sql
import pandas as pd

# 🎨 Page settings
st.set_page_config(
    page_title="GenAI SQL Assistant",
    page_icon="🧠",
    layout="wide"
)

# 🧠 Header
st.markdown("""
# 🧠 GenAI SQL Assistant
Ask your data questions in natural language and get instant answers — powered by GPT and SQL.

> Example: *"What are the top 5 products by revenue in 2024?"*

---
""")

# 📋 Sidebar info
st.sidebar.title("📊 About this App")
st.sidebar.markdown("""
This app uses OpenAI GPT to:
- Translate natural language into SQL
- Query a sample SQLite database
- Display results as charts and tables

Built with ❤️ by Sujithkumar Menon

---
🔐 **API Key is stored securely using Streamlit secrets**
""")

# 💬 User Input
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("💬 Ask a Question")
    user_input = st.text_input(
        "Type your question about the data:",
        placeholder="e.g. Total revenue by product category this year"
    )

with col2:
    if user_input:
        with st.spinner("🤖 Thinking... generating SQL..."):
            schema = get_schema()
            sql = generate_sql(user_input, schema)

            st.markdown("### 🧾 Generated SQL")
            st.code(sql, language="sql")

            result = run_sql(sql)

        if isinstance(result, str):
            st.error(result)
        else:
            st.success("✅ Query executed successfully!")

            st.markdown("### 📋 Results")
            st.dataframe(result, use_container_width=True)

            if result.shape[1] >= 2:
                st.markdown("### 📊 Visualization")
                st.bar_chart(result.set_index(result.columns[0]))

            # Download CSV
            csv = result.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", csv, "query_results.csv", "text/csv")
