import io
import sys
import importlib.util
import streamlit as st
import pandas as pd
from pathlib import Path

# Load kpi_logic directly from goals_app by file path to avoid module name conflicts
_kpi_logic_path = Path(__file__).parent.parent.parent / "goals_app" / "utils" / "kpi_logic.py"
_spec = importlib.util.spec_from_file_location("goals_kpi_logic", _kpi_logic_path)
_kpi_logic = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_kpi_logic)

calculate_operational_goal_rating = _kpi_logic.calculate_operational_goal_rating
calculate_customer_goal_rating     = _kpi_logic.calculate_customer_goal_rating
calculate_innovation_goal_rating   = _kpi_logic.calculate_innovation_goal_rating
calculate_people_goal_rating       = _kpi_logic.calculate_people_goal_rating
GOAL_RATING_COLORS                 = _kpi_logic.GOAL_RATING_COLORS
GOAL_RATING_LABELS                 = _kpi_logic.GOAL_RATING_LABELS

from utils.kpi_mapping import TEMPLATE_MAP


WEIGHTS = {
    "Operational": 0.35,
    "Customer":    0.35,
    "Innovation":  0.20,
    "People":      0.10,
}


def _final_rating(op, cu, inn, ppl) -> float | None:
    vals = {"Operational": op, "Customer": cu, "Innovation": inn, "People": ppl}
    if any(v is None for v in vals.values()):
        return None
    return round(sum(vals[k] * WEIGHTS[k] for k in vals), 2)


def _final_badge(score: float | None) -> str:
    if score is None:
        return "—"
    if score >= 4.5:
        bg, fg = "#14532d", "#ffffff"   # dark green
        label = "Outstanding"
    elif score >= 4.0:
        bg, fg = "#166534", "#dcfce7"   # green
        label = "Exceeding"
    elif score >= 3.0:
        bg, fg = "#713f12", "#fef9c3"   # yellow/amber
        label = "Meeting"
    else:
        bg, fg = "#7f1d1d", "#fee2e2"   # red
        label = "Below"
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 12px;'
        f'border-radius:20px;font-size:0.85rem;font-weight:700;">'
        f'{score} · {label}</span>'
    )


def _badge(rating) -> str:
    if rating is None or (isinstance(rating, float) and str(rating) == 'nan'):
        return "—"
    rating = int(rating)
    bg, fg = GOAL_RATING_COLORS[rating]
    label = GOAL_RATING_LABELS[rating]
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 10px;'
        f'border-radius:20px;font-size:0.8rem;font-weight:600;">'
        f'{rating} · {label}</span>'
    )


def _build_kpi_dict(sap_row: dict, supp_row: dict, sap_map: dict, extra_keys: list) -> dict:
    """Merge SAP values and supplementary values into a kpi_logic dict."""
    result = {}
    for col, key in sap_map.items():
        result[key] = sap_row.get(col)
    for key in extra_keys:
        # Find the template column name for this key
        for col, k in TEMPLATE_MAP.items():
            if k == key:
                val = supp_row.get(col)
                result[key] = float(val) if val is not None and str(val).strip() not in ("", "nan") else None
                break
    return result


def show():
    st.markdown(
        """
        <div class="page-header">
            <h1>🎯 Goal Ratings</h1>
            <p>Automatically calculated 1–5 goal ratings per engineer</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "supp_data" not in st.session_state:
        st.warning("Please upload the KPI Data Template first from the Upload page.")
        return

    parsed = st.session_state.get("parsed")
    supp_df = st.session_state["supp_data"]

    # Period selector only shown if SAP report is also loaded
    if parsed:
        period = st.selectbox("Select Period", options=parsed["periods"], key="goal_period")
    else:
        period = "—"
        st.info("ℹ️ SAP report not loaded — showing ratings based on uploaded KPI data only.")

    results = []
    for _, row in supp_df.iterrows():
        engineer = str(row.get("Engineer", "")).strip()
        if not engineer:
            continue

        # Build case-insensitive column lookup
        row_lower = {str(k).strip().lower(): v for k, v in row.items()}

        # All KPI columns that are percentages (should be 0-100 scale)
        PCT_COLS = {"irt", "apt", "ort", "qms", "nces", "kcs focus", "pulse",
                    "p1 solved", "p2 solved"}

        def get_val(col):
            val = row_lower.get(col.strip().lower())
            try:
                if val is None or str(val).strip() in ("", "nan"):
                    return None
                num = float(val)
                # If Excel stored as % decimal (e.g. 0.8571 instead of 85.71)
                if col.strip().lower() in PCT_COLS and abs(num) <= 1.0:
                    num = round(num * 100, 2)
                return num
            except (ValueError, TypeError):
                return None

        op_vals  = {k: get_val(c) for c, k in TEMPLATE_MAP.items() if k in ["irt","apt","ort","qms","chat","incoming","p1_solved","p2_solved","p1_taken"]}
        cu_vals  = {k: get_val(c) for c, k in TEMPLATE_MAP.items() if k in ["nces","surveys"]}
        inn_vals = {k: get_val(c) for c, k in TEMPLATE_MAP.items() if k in ["kcs_focus","pulse","release_defects","innovation_supportability"]}
        ppl_vals = {k: get_val(c) for c, k in TEMPLATE_MAP.items() if k in ["expert_area","gamification","swarms"]}

        op  = calculate_operational_goal_rating(op_vals)
        cu  = calculate_customer_goal_rating(cu_vals)
        inn = calculate_innovation_goal_rating(inn_vals)
        ppl = calculate_people_goal_rating(ppl_vals)

        results.append({
            "Engineer":     engineer,
            "Operational":  op,
            "Customer":     cu,
            "Innovation":   inn,
            "People":       ppl,
            "Final Rating": _final_rating(op, cu, inn, ppl),
        })

    results_df = pd.DataFrame(results)

    # ── Sort option ────────────────────────────────────────────────────────────
    st.markdown(f"#### Engineer Goal Ratings — {period}")
    sc1, sc2 = st.columns([2, 2])
    with sc1:
        sort_col = st.selectbox("Sort by", options=["Engineer", "Operational", "Customer", "Innovation", "People", "Final Rating"], key="goal_sort_col")
    with sc2:
        sort_order = st.radio("Order", options=["Descending", "Ascending"], horizontal=True, key="goal_sort_order")

    ascending = sort_order == "Ascending"
    results_df = results_df.sort_values(by=sort_col, ascending=ascending, na_position="last").reset_index(drop=True)

    header_cols = st.columns([2, 1.2, 1.2, 1.2, 1.2, 2])
    for col, label in zip(header_cols, ["Engineer", "Operational", "Customer", "Innovation", "People", "Final Rating"]):
        col.markdown(f"**{label}**")

    st.markdown('<hr style="margin:4px 0 8px 0;border-color:#e2e8f0;">', unsafe_allow_html=True)

    for _, row in results_df.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([2, 1.2, 1.2, 1.2, 1.2, 2])
        c1.markdown(f'<p style="margin:6px 0;">{row["Engineer"]}</p>', unsafe_allow_html=True)
        c2.markdown(_badge(row["Operational"]), unsafe_allow_html=True)
        c3.markdown(_badge(row["Customer"]),    unsafe_allow_html=True)
        c4.markdown(_badge(row["Innovation"]),  unsafe_allow_html=True)
        c5.markdown(_badge(row["People"]),      unsafe_allow_html=True)
        c6.markdown(_final_badge(row["Final Rating"]), unsafe_allow_html=True)

    st.markdown("---")

    # ── Export ─────────────────────────────────────────────────────────────────
    export = results_df.copy()

    def _fmt_goal(r):
        try:
            if r is None or (isinstance(r, float) and str(r) == 'nan'):
                return "—"
            return f"{int(r)} · {GOAL_RATING_LABELS[int(r)]}"
        except Exception:
            return "—"

    for col in ["Operational", "Customer", "Innovation", "People"]:
        export[col] = export[col].apply(_fmt_goal)
    export["Final Rating"] = export["Final Rating"].apply(
        lambda r: str(r) if r is not None and str(r) != 'nan' else "—"
    )
    buf = io.BytesIO()
    export.to_excel(buf, index=False)
    st.download_button(
        label="⬇️ Download Goal Ratings as Excel",
        data=buf.getvalue(),
        file_name=f"goal_ratings_{period.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
