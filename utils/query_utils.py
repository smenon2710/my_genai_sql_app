import sqlite3
import pandas as pd
import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔧 Get absolute path to DB file (portable for deployment)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "schema", "sample_data.db")

# 🧠 Generate SQL using GPT
def generate_sql(nl_query, schema):
    prompt = f"""
You are a SQL generator. ONLY return the raw SQL query. No explanation, no markdown, no commentary.

Here is the schema:
{schema}

User request:
{nl_query}
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    # Clean SQL from markdown/code blocks if any
    matches = re.findall(r"```sql(.*?)```", content, re.DOTALL)
    if matches:
        cleaned_sql = matches[0].strip()
    else:
        cleaned_sql = content  # fallback if no markdown

    return cleaned_sql

# 🔍 Run SQL query against SQLite DB
def run_sql(sql):
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(sql, conn)
        return df
    except Exception as e:
        return f"❌ SQL Error: {e}"
    finally:
        conn.close()

# 📜 Extract DB Schema for the LLM
def get_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema = ""
    for t in tables:
        cursor.execute(f"PRAGMA table_info({t[0]})")
        cols = cursor.fetchall()
        schema += f"\nTable {t[0]}:\n"
        for col in cols:
            schema += f"  {col[1]} ({col[2]})\n"
    conn.close()
    return schema
