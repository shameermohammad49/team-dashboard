import streamlit as st
import pandas as pd
from utils.parser import get_pivot


def show():
    st.markdown(
        """
        <div class="page-header">
            <h1>🏆 Engineer Ranking</h1>
            <p>See how engineers rank for each KPI in the selected period</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "parsed" not in st.session_state:
        st.warning("Please upload a report first from the Upload page.")
        return

    parsed = st.session_state["parsed"]

    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox("Select Period", options=parsed["periods"], key="rank_period")
    with col2:
        kpi = st.selectbox("Select KPI", options=parsed["kpis"], key="rank_kpi")

    pivot = get_pivot(parsed, period)
    if pivot.empty or kpi not in pivot.columns:
        st.info("No data available for the selected period / KPI.")
        return

    ranking = (
        pivot[["Engineer", kpi]]
        .dropna(subset=[kpi])
        .sort_values(kpi, ascending=False)
        .reset_index(drop=True)
    )
    ranking.index += 1
    ranking.index.name = "Rank"
    ranking[kpi] = ranking[kpi].apply(lambda x: round(x, 2))

    def highlight_top(row):
        if row.name == 1:
            return ["background-color:#fef9c3;font-weight:700"] * len(row)
        elif row.name == 2:
            return ["background-color:#f0fdf4;font-weight:600"] * len(row)
        elif row.name == 3:
            return ["background-color:#eff6ff;font-weight:600"] * len(row)
        return [""] * len(row)

    # Format value as string so Streamlit left-aligns it
    fmt_fn = (lambda x: f"{x:.0f}") if kpi.strip().startswith("#") else (lambda x: f"{x:.2f}")
    ranking[kpi] = ranking[kpi].apply(fmt_fn)

    st.markdown(f"#### {kpi} — {period}")
    st.dataframe(
        ranking.style.apply(highlight_top, axis=1),
        use_container_width=True,
    )

    st.markdown("---")

    # ── Quick all-KPI ranking table ────────────────────────────────────────────
    st.markdown("#### All KPIs — Engineer Rankings")
    kpi_cols = [c for c in pivot.columns if c != "Engineer"]
    all_ranks = pivot[["Engineer"]].copy()
    for k in kpi_cols:
        if k in pivot.columns:
            all_ranks[k] = pivot[k].rank(ascending=False, method="min").astype("Int64")
    st.dataframe(all_ranks, use_container_width=True, hide_index=True)
