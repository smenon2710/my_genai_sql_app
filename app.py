# app.py
import streamlit as st
import pandas as pd
import altair as alt
from openai import OpenAIError

from utils.query_utils import (
    build_database, lock_read_only, get_schema, generate_sql,
    run_sql, friendly_api_error, is_write_attempt,
)
from utils.load_utils import load_table, list_sheets, is_csv
from utils.display_utils import chart_plan, suggest_questions, summarize

st.set_page_config(page_title="GenAI SQL Assistant", layout="wide")
st.title("🤖 GenAI SQL Assistant")

# Identical questions on identical data reuse the earlier answer instead of
# paying for another model call
@st.cache_data(ttl=3600, max_entries=500, show_spinner=False)
def cached_sql(question, schema, failed_sql=None, error=None):
    return generate_sql(question, schema, failed_sql, error)

def load_upload(uploaded_file, sheet):
    """Parse the upload and build this session's database, once per file/sheet."""
    data_key = (uploaded_file.file_id, sheet)
    if st.session_state.get("data_key") == data_key:
        return

    df = load_table(uploaded_file, uploaded_file.name, sheet)
    if df.empty or len(df.columns) == 0:
        raise ValueError("no table was found in the file")

    conn = build_database(df)
    schemas = {examples: get_schema(conn, df, examples) for examples in (True, False)}
    lock_read_only(conn)

    if "conn" in st.session_state:
        st.session_state["conn"].close()
    st.session_state.update(data_key=data_key, df=df, conn=conn, schemas=schemas, question="")

def answer(question, schema, conn):
    """Generate SQL and run it, giving the model one chance to fix a failed query."""
    sql = cached_sql(question, schema)
    try:
        return sql, run_sql(conn, sql)
    except Exception as first_error:
        if is_write_attempt(first_error):
            raise
        sql = cached_sql(question, schema, sql, str(first_error))
        return sql, run_sql(conn, sql)

def show_chart(result):
    plan = chart_plan(result)
    if plan is None:
        return

    measure = plan.measures[0]
    if len(plan.measures) > 1:
        measure = st.selectbox("Chart", plan.measures)

    # Fixed field names: result columns like "SUM(x)" or "a.b" confuse Vega-Lite
    data = pd.DataFrame({"label": result[plan.label], "value": result[measure]})
    tooltip = [alt.Tooltip("label", title=plan.label), alt.Tooltip("value", title=measure, format=",.4~f")]
    if plan.kind == "line":
        data["label"] = pd.to_datetime(data["label"])
        chart = alt.Chart(data).mark_line(point=True).encode(
            x=alt.X("label:T", title=plan.label),
            y=alt.Y("value:Q", title=measure),
            tooltip=tooltip,
        )
    else:
        # Horizontal so long labels stay readable; sort=None keeps the order the
        # query returned, e.g. "highest first"
        chart = alt.Chart(data).mark_bar().encode(
            y=alt.Y("label:N", sort=None, title=plan.label),
            x=alt.X("value:Q", title=measure),
            tooltip=tooltip,
        )
    st.altair_chart(chart)

def use_suggestion(question):
    st.session_state["question"] = question

share_values = st.sidebar.checkbox(
    "Share example values with the model",
    value=True,
    help="Sends a few example values per column with your question, which makes the SQL "
         "more accurate. Turn off to send only column names and types.",
)

uploaded_file = st.file_uploader("📁 Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    sheet = 0
    if not is_csv(uploaded_file.name):
        if st.session_state.get("sheets_for") != uploaded_file.file_id:
            try:
                st.session_state["sheets"] = list_sheets(uploaded_file)
            except Exception as e:
                st.error(f"❌ Could not read the workbook: {e}")
                st.stop()
            st.session_state["sheets_for"] = uploaded_file.file_id
        sheets = st.session_state["sheets"]
        sheet = st.selectbox("Sheet", sheets) if len(sheets) > 1 else sheets[0]

    try:
        load_upload(uploaded_file, sheet)
    except Exception as e:
        st.error(f"❌ Could not read the file: {e}")
        st.stop()

    df = st.session_state["df"]
    conn = st.session_state["conn"]
    schema = st.session_state["schemas"][share_values]

    st.success("✅ File uploaded successfully")
    st.write(f"Preview ({len(df):,} rows, {len(df.columns)} columns):")
    st.dataframe(df)

    user_input = st.text_input(
        "🔍 Ask your question (e.g., 'Show average sales by region')", key="question"
    )

    suggestions = suggest_questions(df)
    for column, suggestion in zip(st.columns(len(suggestions)), suggestions):
        column.button(suggestion, on_click=use_suggestion, args=(suggestion,))

    if user_input:
        try:
            with st.spinner("Generating SQL..."):
                sql, result = answer(user_input, schema, conn)
        except (OpenAIError, RuntimeError) as e:
            st.error(f"❌ {friendly_api_error(e)}")
            st.stop()
        except Exception as e:
            if is_write_attempt(e):
                st.error("❌ Only questions that read the data are supported; it cannot be changed.")
            else:
                st.error(f"❌ Failed to run SQL: {e}")
            st.stop()

        st.code(sql, language="sql")

        if result.empty:
            st.warning("⚠️ Query executed successfully, but returned no results.")
        else:
            summary = summarize(result)
            if summary:
                # Escaped so a label like "$5 plan" is not rendered as LaTeX
                st.info(summary.replace("$", "\\$"))
            st.dataframe(result)
            show_chart(result)
