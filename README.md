# GenAI SQL Assistant

Upload a CSV or Excel file, ask a question in plain English, and get the SQL, the result table, a one-line summary and, where it fits, a chart.

The file is loaded into a private in-memory SQLite table (`uploaded_data`). The table's schema and your question are sent to an LLM through [OpenRouter](https://openrouter.ai), which returns a SQLite query that is then run locally.

## What it does

- **Reads formatted spreadsheets**: finds the real header row under title rows and drops empty padding around the table. Workbooks with several sheets get a sheet picker.
- **Suggests questions**: starter questions built from your column names, shown as buttons under the question box.
- **Recovers from bad SQL**: if a query fails, the error is sent back to the model once for a corrected query.
- **Summarises the result**: one line naming the highest and lowest rows, shown when the result has one row per label. It is calculated in the app, not written by the model.
- **Charts only when it helps**: a bar chart for one label column with numeric columns (up to 30 rows, in the order the query returned), or a line chart when the labels are dates. With several numeric columns you pick which one to plot. Other results get no chart.

## What leaves your machine

Sent to the model with each question:

- column names and types, and the row count;
- with "Share example values with the model" ticked in the sidebar (the default): up to 5 example values per text column and the minimum and maximum of each number or date column.

Untick the box to send only names, types and the row count; the SQL may be less accurate. Full rows and query results are never sent.

## Safeguards

- **Private per session**: each browser session has its own in-memory database, so visitors cannot see or overwrite each other's uploads. Nothing is written to disk.
- **Read-only**: generated SQL can only read. Anything else (`DELETE`, `DROP`, `ATTACH`, `PRAGMA` and so on) is refused by SQLite.
- **Spend**: the same question on the same data is answered from a one-hour cache instead of a new model call. This does not cap spend on a public app; set a credit limit on the key at https://openrouter.ai/keys.

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

## Deploy on Streamlit Community Cloud

Create the app at https://share.streamlit.io from this repository (`smenon2710/my_genai_sql_app`), branch `main`, main file `app.py`, Python 3.12. Under Advanced settings, add the secret:

```toml
OPENROUTER_API_KEY = "your-openrouter-key"
```

Every push to `main` then redeploys the app. The repository and main file of an existing app cannot be changed; to move an app, delete it and create it again.

## Finding this app's calls in OpenRouter

Every request carries OpenRouter's [app attribution](https://openrouter.ai/docs/app-attribution) headers, set once on the client in `utils/query_utils.py`:

| Header | Value | Purpose |
|---|---|---|
| `HTTP-Referer` | `https://github.com/smenon2710/my_genai_sql_app` | Identifies the app; OpenRouter records it as the call's origin |
| `X-OpenRouter-Title` | `GenAI SQL Assistant` | Display name for the app |
| `X-OpenRouter-App-Visibility` | `hidden` | Keeps the app out of public rankings and app pages |

OpenRouter attributes each call to the app "GenAI SQL Assistant"; its usage is at https://openrouter.ai/apps?url=https://github.com/smenon2710/my_genai_sql_app. To check a single call, look it up by id; the response includes `app_id` and `origin`:

```bash
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  "https://openrouter.ai/api/v1/generation?id=<generation id>"
```

Visibility is fixed when OpenRouter first sees the app. Making it public later means contacting OpenRouter support; removing the header is not enough.

## Files

- `app.py` — Streamlit UI: upload, sheet picker, question box, results, summary and chart.
- `utils/load_utils.py` — reads the upload, skipping title rows and empty padding around the table.
- `utils/query_utils.py` — builds the read-only database, describes the schema, asks the model for SQL, runs the query.
- `utils/display_utils.py` — decides whether a result suits a chart, writes the summary line, suggests questions.
- `create_db.py` — optional: builds a sample database at `schema/sample_data.db` (products and orders). The app itself does not use it.
