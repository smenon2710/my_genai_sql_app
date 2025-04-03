import os
import re
import pandas as pd
import pandasql as ps
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get API key from .env file
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("🚨 OPENAI_API_KEY not found. Please set it in your .env file.")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Extract the schema (table name and columns) from the dataframe
def get_schema(df: pd.DataFrame, table_name="data") -> str:
    column_info = [f"{col} ({str(dtype)})" for col, dtype in zip(df.columns, df.dtypes)]
    schema_str = f"Table: {table_name}\nColumns:\n" + "\n".join(column_info)
    return schema_str

# Use OpenAI to generate SQL query based on user input and schema
def generate_sql(prompt: str, schema: str) -> str:
    system_prompt = (
        "You are an expert data analyst who writes SQLite SQL queries. "
        "Given the table schema and a user's question, generate the SQL query "
        "that answers it. Only return valid SQL code. Do not add explanations."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{schema}\n\nUser question: {prompt}"}
        ],
        temperature=0,
    )

    sql_code = response.choices[0].message.content.strip()

    # Extract SQL from markdown/code block if needed
    match = re.search(r"```sql\s*(.*?)\s*```", sql_code, re.DOTALL)
    return match.group(1) if match else sql_code

# Run the generated SQL query on the user-uploaded dataframe
def run_sql(df: pd.DataFrame, sql: str) -> pd.DataFrame:
    try:
        result = ps.sqldf(sql, {"data": df})
        return result
    except Exception as e:
        raise RuntimeError(f"❌ SQL Execution Error: {e}")
