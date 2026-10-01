# utils/display_utils.py
import re
from dataclasses import dataclass
import pandas as pd

# More bars than this stop being readable
MAX_BARS = 30
MAX_LINE_POINTS = 2000
# A text column with more distinct values than this is not a useful grouping
MAX_GROUPS = 50
SMALL_GROUP = 12
MAX_SUMMARY_MEASURES = 2

DATE_LABEL = re.compile(r"^\d{4}-\d{2}(-\d{2})?([ T].*)?$")
ID_NAME = re.compile(r"(^|[\s_])id$", re.IGNORECASE)
HEADLINE_NAMES = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (r"sales|revenue|amount", r"profit|total", r"quantity|units|count")
]

@dataclass
class ChartPlan:
    kind: str        # "bar" or "line"
    label: str       # column on the x axis
    measures: list   # numeric columns that can go on the y axis

def _is_measure(series):
    return pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series)

def chart_plan(result):
    """Decide whether a query result suits a chart, and which kind.

    A result is chartable when it is one label column plus numeric columns,
    with one row per label: bars for categories, a line for dates.
    """
    if len(result) < 2 or result.shape[1] < 2:
        return None

    labels = [col for col in result.columns if not _is_measure(result[col])]
    measures = [col for col in result.columns if _is_measure(result[col]) and result[col].notna().any()]
    if len(labels) != 1 or not measures:
        return None

    label = labels[0]
    values = result[label]
    if values.isna().any() or values.duplicated().any():
        return None

    if values.astype(str).str.match(DATE_LABEL).all():
        if len(result) <= MAX_LINE_POINTS and pd.to_datetime(values, errors="coerce").notna().all():
            return ChartPlan("line", label, measures)
        return None

    if len(result) > MAX_BARS:
        return None
    return ChartPlan("bar", label, measures)

def _number(value):
    return f"{value:,.2f}".rstrip("0").rstrip(".") if value % 1 else f"{value:,.0f}"

def summarize(result):
    """One line naming the highest and lowest rows of a result, or None.

    Worked out here rather than by the model: small models misread the largest
    value in a list of numbers often enough to matter.
    """
    if len(result) < 2:
        return None
    labels = [col for col in result.columns if not _is_measure(result[col])]
    measures = [
        col for col in result.columns
        if _is_measure(result[col]) and result[col].notna().any() and not ID_NAME.search(col)
    ]
    # Repeated labels mean row-level data, where "highest for X" would be ambiguous
    if not labels or not measures or result.duplicated(subset=labels).any():
        return None

    def describe(row):
        return ", ".join(str(row[col]) for col in labels)

    sentences = []
    for col in measures[:MAX_SUMMARY_MEASURES]:
        high, low = result.loc[result[col].idxmax()], result.loc[result[col].idxmin()]
        if high[col] == low[col]:
            continue
        sentences.append(
            f"{col} is highest for {describe(high)} ({_number(high[col])}) "
            f"and lowest for {describe(low)} ({_number(low[col])})."
        )
    return " ".join(sentences) or None

def suggest_questions(df):
    """A few starter questions built from the column names and types."""
    measures = [col for col in df.columns if _is_measure(df[col]) and not ID_NAME.search(col)]
    dates = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    groups = [
        col for col in df.columns
        if col not in measures and col not in dates and not _is_measure(df[col])
        and 2 <= df[col].nunique() <= MAX_GROUPS
    ]

    if not measures:
        return ["How many rows are there?"] + [f"How many rows per {col}?" for col in groups[:2]]

    # Prefer a column that sounds like the headline number, best matches first
    measure = measures[0]
    for pattern in HEADLINE_NAMES:
        match = next((col for col in measures if pattern.search(col)), None)
        if match:
            measure = match
            break
    total = measure if measure.lower().startswith("total") else f"Total {measure}"

    questions = []
    if groups:
        sizes = {col: df[col].nunique() for col in groups}
        # A handful of groups reads well as a breakdown; the widest column suits a top 5
        breakdown = next((col for col in groups if sizes[col] <= SMALL_GROUP), min(groups, key=sizes.get))
        widest = max(groups, key=sizes.get)
        questions.append(f"{total} by {breakdown}")
        if widest != breakdown and sizes[widest] > 5:
            questions.append(f"Top 5 {widest} by {total}")
    if dates:
        questions.append(f"Monthly {total} over time")
    if not questions:
        questions.append(f"What is the total and average {measure}?")
    return questions
