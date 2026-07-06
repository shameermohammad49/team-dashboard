"""
Parses the SAP Analytics Cloud pivot Excel report.

Structure:
  Row 0: Measures  (KPI names, repeated across time columns)
  Row 1: Year      (Totals, 2026, ...)
  Row 2: Quarter   (Totals, Q3, Q1, Q2, ...)
  Row 3: Month     (Totals, Totals, Jul, Totals, Feb, Mar, ...)
  Row 4: Engineer  (label row)
  Row 5+: data rows (one per engineer)

Returns a dict:
  {
    "periods": ["Totals", "2026|Q3|Jul", "2026|Q1|Totals", ...],
    "kpis": ["% Net CES", "% IRT", ...],
    "data": DataFrame with columns [Engineer, period, kpi, value]
  }
"""

import re
import pandas as pd
import numpy as np


def _clean_value(v, kpi_name=""):
    if pd.isna(v):
        return None
    s = str(v).strip().replace("%", "").replace(",", "").strip()
    try:
        num = float(s)
        # Excel always stores % formatted cells as decimals (0.9691 = 96.91%)
        if kpi_name.strip().startswith("%"):
            num = round(num * 100, 2)
        else:
            num = round(num, 2)
        return num
    except ValueError:
        return None


def parse_report(file) -> dict:
    raw = pd.read_excel(file, header=None)

    # Find the row that starts with "Engineer"
    eng_row_idx = None
    for i, row in raw.iterrows():
        if str(row.iloc[0]).strip().lower() == "engineer":
            eng_row_idx = i
            break

    if eng_row_idx is None:
        raise ValueError("Could not find 'Engineer' row in the file.")

    # Header rows are above the Engineer row
    measure_row  = raw.iloc[eng_row_idx - 4] if eng_row_idx >= 4 else raw.iloc[0]
    year_row     = raw.iloc[eng_row_idx - 3] if eng_row_idx >= 3 else None
    quarter_row  = raw.iloc[eng_row_idx - 2] if eng_row_idx >= 2 else None
    month_row    = raw.iloc[eng_row_idx - 1] if eng_row_idx >= 1 else None

    # Data rows
    data_rows = raw.iloc[eng_row_idx + 1:].reset_index(drop=True)
    data_rows = data_rows.dropna(subset=[data_rows.columns[0]])
    data_rows = data_rows[data_rows.iloc[:, 0].astype(str).str.strip() != ""]

    # Build column labels: forward-fill year, quarter, month
    n_cols = raw.shape[1]

    def ffill_row(row):
        vals = list(row)
        last = ""
        result = []
        for v in vals:
            s = str(v).strip() if not pd.isna(v) else ""
            if s and s.lower() not in ("nan", "none"):
                last = s
            result.append(last)
        return result

    years    = ffill_row(year_row)    if year_row is not None    else [""] * n_cols
    quarters = ffill_row(quarter_row) if quarter_row is not None else [""] * n_cols
    months   = ffill_row(month_row)   if month_row is not None   else [""] * n_cols
    measures = list(measure_row)

    # Build period labels (skip col 0 = Engineer name)
    periods = []
    for i in range(1, n_cols):
        y = years[i]
        q = quarters[i]
        m = months[i]
        # Build a readable period label
        parts = []
        if y and y.lower() not in ("totals", "nan"):
            parts.append(y)
        if q and q.lower() not in ("totals", "nan"):
            parts.append(q)
        if m and m.lower() not in ("totals", "nan"):
            parts.append(m)
        label = " | ".join(parts) if parts else "Totals"
        # Distinguish column-level "Totals" entries
        if not parts:
            if q.lower() == "totals" and m.lower() == "totals":
                label = f"{y} Total" if y and y.lower() != "totals" else "Grand Total"
            elif m.lower() == "totals":
                label = f"{q} Total" if q and q.lower() != "totals" else f"{y} Total"
        periods.append(label)

    # KPI names (forward-fill measures row, skip col 0)
    kpi_labels = []
    last_kpi = ""
    for i in range(1, n_cols):
        m = str(measures[i]).strip() if not pd.isna(measures[i]) else ""
        if m and m.lower() not in ("nan", "none"):
            last_kpi = m
        kpi_labels.append(last_kpi)

    # Build long-format DataFrame
    records = []
    totals_records = []
    for _, row in data_rows.iterrows():
        engineer = str(row.iloc[0]).strip()
        if not engineer or engineer.lower() in ("nan", "none"):
            continue
        is_totals = engineer.lower() == "totals"
        for i in range(1, n_cols):
            val = _clean_value(row.iloc[i], kpi_labels[i - 1])
            entry = {
                "Engineer": engineer,
                "Period":   periods[i - 1],
                "KPI":      kpi_labels[i - 1],
                "Value":    val,
            }
            if is_totals:
                totals_records.append(entry)
            else:
                records.append(entry)

    df = pd.DataFrame(records)
    df_totals = pd.DataFrame(totals_records)
    unique_periods = list(dict.fromkeys(periods))
    unique_kpis    = list(dict.fromkeys(kpi_labels))

    return {
        "periods":  unique_periods,
        "kpis":     unique_kpis,
        "data":     df,
        "totals":   df_totals,
    }


def get_totals_row(parsed: dict, period: str) -> dict:
    """Return team totals row for a given period as {KPI: value}."""
    df = parsed.get("totals", pd.DataFrame())
    if df.empty:
        return {}
    sub = df[df["Period"] == period]
    return dict(zip(sub["KPI"], sub["Value"]))


def get_pivot(parsed: dict, period: str) -> pd.DataFrame:
    """Return a wide DataFrame: rows=Engineers, columns=KPIs for a given period."""
    df = parsed["data"]
    sub = df[df["Period"] == period].copy()
    if sub.empty:
        return pd.DataFrame()
    pivot = sub.pivot_table(index="Engineer", columns="KPI", values="Value", aggfunc="first")
    pivot = pivot.reset_index()
    pivot.columns.name = None
    ordered_cols = ["Engineer"] + [k for k in parsed["kpis"] if k in pivot.columns]
    return pivot[[c for c in ordered_cols if c in pivot.columns]]
