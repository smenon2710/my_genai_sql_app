# utils/query_utils.py
import sqlite3
import os
import re
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError

load_dotenv()
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
TABLE_NAME = "uploaded_data"

# How many distinct example values per text column are shown to the model
EXAMPLE_VALUES = 5

# The only things a generated query is allowed to do
READ_ONLY_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    sqlite3.SQLITE_RECURSIVE,
}

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")
        # OpenRouter exposes an OpenAI-compatible API, so the OpenAI SDK works as-is
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            # App attribution: OpenRouter tags every call with this app so it can be
            # picked out in the account's activity and analytics
            default_headers={
                "HTTP-Referer": "https://github.com/smenon2710/my_genai_sql_app",
                "X-OpenRouter-Title": "GenAI SQL Assistant",
                # Keep the app out of OpenRouter's public rankings and app pages
                "X-OpenRouter-App-Visibility": "hidden",
            },
        )
    return _client

def friendly_api_error(error):
    """A message for the user when the model call fails."""
    if isinstance(error, RuntimeError):
        return f"The app is not configured: {error} Add it to .env or the app's secrets."
    if isinstance(error, AuthenticationError):
        return "OpenRouter rejected the API key. Check OPENROUTER_API_KEY."
    if isinstance(error, RateLimitError):
        return "OpenRouter is rate limiting requests or the key is out of credit. Try again shortly."
    if isinstance(error, APIConnectionError):
        return "Could not reach OpenRouter. Check the network connection and try again."
    return f"The model request failed: {error}"

def _authorize_read_only(action, *_):
    return sqlite3.SQLITE_OK if action in READ_ONLY_ACTIONS else sqlite3.SQLITE_DENY

def build_database(df):
    """Load the table into a private in-memory database that only allows reads."""
    # Streamlit reruns the script on different threads within one session
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    conn.commit()
    return conn

def lock_read_only(conn):
    conn.set_authorizer(_authorize_read_only)

def is_write_attempt(error):
    return "not authorized" in str(error)

def _example(value):
    text = str(value)
    return repr(text if len(text) <= 40 else text[:37] + "...")

def get_schema(conn, df, include_examples=True):
    """Describe the table for the model: columns, types and optionally example values."""
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info("{TABLE_NAME}");')
    columns = cursor.fetchall()

    schema_info = f'Table: "{TABLE_NAME}" ({len(df)} rows)\n'
    for col in columns:
        name, sql_type = col[1], col[2]
        # Quoted so the model copies names with spaces as valid identifiers
        line = f' - "{name}" ({sql_type})'
        values = df[name].dropna()
        if include_examples and not values.empty:
            if pd.api.types.is_bool_dtype(values) or not (
                pd.api.types.is_numeric_dtype(values) or pd.api.types.is_datetime64_any_dtype(values)
            ):
                distinct = values.unique()
                shown = ", ".join(_example(v) for v in distinct[:EXAMPLE_VALUES])
                line += f" e.g. {shown} ({len(distinct)} distinct values)"
            else:
                low, high = values.min(), values.max()
                if pd.api.types.is_float_dtype(values):
                    # Trim float noise such as 110.00000000000001
                    low, high = f"{low:.10g}", f"{high:.10g}"
                line += f" from {low} to {high}"
        schema_info += line + "\n"
    return schema_info

def generate_sql(question, schema, failed_sql=None, error=None):
    prompt = f"""
You are an expert data analyst.
Given the following database schema:
{schema}

Write an SQLite SQL query for the question: "{question}"
Always wrap table and column names in double quotes, exactly as written in the schema.
Only return valid SQL and nothing else.
"""
    if failed_sql:
        prompt += f"""
Your previous attempt was:
{failed_sql}

It failed with this error: {error}
Return a corrected query.
"""

    response = get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
    )

    sql = response.choices[0].message.content.strip()
    # Models often wrap the query in a ```sql fence despite the prompt
    fenced = re.search(r"```(?:sql|sqlite)?\s*(.*?)```", sql, re.DOTALL | re.IGNORECASE)
    if fenced:
        sql = fenced.group(1).strip()
    return sql

def run_sql(conn, sql):
    return pd.read_sql_query(sql, conn)
