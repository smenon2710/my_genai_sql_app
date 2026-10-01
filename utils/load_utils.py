# utils/load_utils.py
import csv
import io
import pandas as pd

# How many rows at the top of the file to look at when finding the header
SCAN_ROWS = 50

def find_header_row(fill_counts):
    """Index of the first row that is at least half as wide as the widest row.

    Title rows and blank spacer rows above a table only fill a cell or two,
    while the real header row fills every column of the table.
    """
    widest = max(fill_counts, default=0)
    if widest == 0:
        return 0
    for i, count in enumerate(fill_counts):
        if count >= widest / 2:
            return i
    return 0

def load_table(file, filename):
    """Read an uploaded CSV/Excel file, skipping any title rows above the table."""
    is_csv = filename.lower().endswith(".csv")

    if is_csv:
        head = file.read().decode("utf-8-sig", errors="replace")
        rows = list(csv.reader(io.StringIO(head)))[:SCAN_ROWS]
        fill_counts = [sum(1 for cell in row if cell.strip()) for row in rows]
    else:
        raw = pd.read_excel(file, header=None, nrows=SCAN_ROWS)
        fill_counts = raw.notna().sum(axis=1).tolist()

    header_row = find_header_row(fill_counts)

    file.seek(0)
    if is_csv:
        df = pd.read_csv(file, skiprows=header_row)
    else:
        df = pd.read_excel(file, header=header_row)

    # Drop the empty padding columns/rows that formatted sheets leave around the table
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all").reset_index(drop=True)
    df.columns = [str(col).strip() for col in df.columns]
    return df
