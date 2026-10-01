# utils/query_utils.py
import sqlite3
import os
import re
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
# OpenRouter exposes an OpenAI-compatible API, so the OpenAI SDK works as-is
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

def get_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema_info = ""
    for table_name in tables:
        table_name = table_name[0]
        cursor.execute(f'PRAGMA table_info("{table_name}");')
        columns = cursor.fetchall()
        schema_info += f'Table: "{table_name}"\n'
        for col in columns:
            # Quoted so the model copies names with spaces as valid identifiers
            schema_info += f' - "{col[1]}" ({col[2]})\n'

    conn.close()
    return schema_info

def generate_sql(question, schema):
    prompt = f"""
You are an expert data analyst.
Given the following database schema:
{schema}

Write an SQLite SQL query for the question: "{question}"
Always wrap table and column names in double quotes, exactly as written in the schema.
Only return valid SQL and nothing else.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    sql = response.choices[0].message.content.strip()
    # Models often wrap the query in a ```sql fence despite the prompt
    fenced = re.search(r"```(?:sql|sqlite)?\s*(.*?)```", sql, re.DOTALL | re.IGNORECASE)
    if fenced:
        sql = fenced.group(1).strip()
    return sql

def run_sql(db_path, sql):
    conn = sqlite3.connect(db_path)
    try:
        result = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return result