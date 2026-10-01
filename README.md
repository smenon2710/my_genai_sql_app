# GenAI SQL Assistant

Upload a CSV or Excel file, ask a question in plain English, and get the SQL, the result table and a bar chart.

The file is loaded into a local SQLite table (`uploaded_data`). The table's schema and your question are sent to an LLM through [OpenRouter](https://openrouter.ai), which returns a SQLite query that is then run locally. Only the schema (column names and types) and your question leave your machine, not the data rows.

## Setup

Requires Python 3.12.

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then put your OpenRouter key in .env
```

Get a key at https://openrouter.ai/keys. To use a different model, set `OPENROUTER_MODEL` in `.env` (default: `openai/gpt-4o-mini`).

## Run

```bash
streamlit run app.py
```

Then open http://localhost:8501.

## Files

- `app.py` — Streamlit UI: upload, question box, results and chart.
- `utils/load_utils.py` — reads the upload, skipping title rows and empty padding around the table.
- `utils/query_utils.py` — reads the schema, asks the model for SQL, runs the query.
- `create_db.py` — optional: builds a sample database at `schema/sample_data.db` (products and orders). The app itself does not use it.
- `uploaded_data.db` — created at runtime from your upload; gitignored.
