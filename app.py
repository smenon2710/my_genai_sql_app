import streamlit as st
import pandas as pd
import openai
from pandasql import sqldf
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="GenAI Excel/CSV Analyst", layout="wide")
st.title("🧠 GenAI Analyst: Ask Questions About Your File")
st.write("Upload a CSV or Excel file and ask anything. No SQL needed.")

# Upload section
uploaded_file = st.file_uploader("📁 Upload CSV or Excel", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("✅ File uploaded successfully")
    st.write("Preview:")
    st.dataframe(df.head(), use_container_width=True)

    # Generate schema
    def get_schema(df):
        schema_str = ""
        for col in df.columns:
            dtype = str(df[col].dtype)
            schema_str += f"{col} ({dtype})\n"
        return schema_str

    schema = get_schema(df)

    # User query
    st.markdown("---")
    user_query = st.text_input("🔍 Ask a question about your file")

    if user_query:
        with st.spinner("🤖 Thinking..."):
            prompt = f"""
You are a data assistant. Write a SQL query that runs on a pandas DataFrame named `df`.
Schema:
{schema}

User question: {user_query}
Only return valid SQL syntax for use with pandasql.
"""
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0
                )
                sql = response.choices[0].message.content.strip()
                st.markdown("### 🧾 Generated SQL")
                st.code(sql, language="sql")

                # Run SQL
                result = sqldf(sql, locals())
                st.success("✅ Query executed")
                st.dataframe(result, use_container_width=True)

                if result.shape[1] >= 2:
                    try:
                        st.bar_chart(result.set_index(result.columns[0]))
                    except Exception as e:
                        st.warning("⚠️ Could not render chart")

                # Download button
                csv = result.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Download Result as CSV", csv, "query_result.csv", "text/csv")

            except Exception as e:
                st.error(f"Error: {e}")
else:
    st.info("⬆️ Upload a file to get started")
