# utils/query_utils.py
import sqlite3
import os
import re
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

def get_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema_info = ""
    for table_name in tables:
        table_name = table_name[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        schema_info += f"Table: {table_name}\n"
        for col in columns:
            schema_info += f" - {col[1]} ({col[2]})\n"

    conn.close()
    return schema_info

def generate_sql(question, schema):
    prompt = f"""
You are an expert data analyst.
Given the following database schema:
{schema}

Write an SQLite SQL query for the question: "{question}"
Only return valid SQL and nothing else.
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()

def run_sql(db_path, sql):
    conn = sqlite3.connect(db_path)
    try:
        result = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return result