# app.py
import streamlit as st
from utils.query_utils import get_schema, generate_sql, run_sql
import pandas as pd

st.set_page_config(page_title="GenAI SQL Assistant", layout="wide")
st.title("🧠💬 Natural Language to SQL Dashboard")

user_input = st.text_input("Ask your data a question:")

if user_input:
    with st.spinner("Generating SQL..."):
        schema = get_schema()
        sql = generate_sql(user_input, schema)
        st.code(sql, language='sql')

        result = run_sql(sql)
        if isinstance(result, str):
            st.error(f"Error: {result}")
        else:
            st.dataframe(result)
            if result.shape[1] >= 2:
                st.bar_chart(result.set_index(result.columns[0]))
