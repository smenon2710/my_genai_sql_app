import sqlite3
import os
import re
import pandas as pd
import tempfile
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 🔐 Load OpenAI Key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔧 Generate SQLite schema from uploaded DataFrame
def get_schema_from_db(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema = ""
    for table_name in tables:
        table_name = table_name[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        schema += f"Table: {table_name}\n"
        for col in columns:
            schema += f" - {col[1]} ({col[2]})\n"
    return schema

# 🧠 Generate SQL from user prompt and schema
def generate_sql(prompt, schema):
    full_prompt = f"""
You are an expert SQL assistant. 
Generate a SQLite SQL query for the user based on the following schema:

{schema}

Question: {prompt}
SQL:
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful SQL assistant."},
            {"role": "user", "content": full_prompt},
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()

# ▶️ Run SQL query and return results as DataFrame
def run_sql(conn, sql):
    try:
        df = pd.read_sql_query(sql, conn)
        return df
    except Exception as e:
        st.error(f"Error executing SQL: {e}")
        return pd.DataFrame()

# 💾 Save DataFrame to SQLite
def save_to_sqlite(df, db_path, table_name):
    try:
        conn = sqlite3.connect(db_path)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Failed to save to SQLite: {e}")

# 🧽 Clean table names
def clean_table_name(name):
    return re.sub(r'\W+', '_', name).lower()
