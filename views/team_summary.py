import streamlit as st
import pandas as pd
from utils.parser import get_pivot, get_totals_row


def show():
    st.markdown(
        """
        <div class="page-header">
            <h1>📊 Team Summary</h1>
            <p>Team-level KPI values and engineer breakdown for the selected period</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "parsed" not in st.session_state:
        st.warning("Please upload a report first from the Upload page.")
        return

    parsed = st.session_state["parsed"]

    period = st.selectbox("Select Period", options=parsed["periods"], key="summary_period")

    pivot = get_pivot(parsed, period)
    totals = get_totals_row(parsed, period)

    if pivot.empty:
        st.info("No data available for the selected period.")
        return

    kpi_cols = [c for c in pivot.columns if c != "Engineer"]

    # ── Team totals row (from report) ──────────────────────────────────────────
    st.markdown("#### Team Total")
    cols = st.columns(min(len(kpi_cols), 4))
    for i, kpi in enumerate(kpi_cols):
        val = totals.get(kpi)
        display = f"{val:,.2f}" if val is not None else "—"
        cols[i % 4].metric(kpi, display)

    st.markdown("---")

    # ── All engineers table ────────────────────────────────────────────────────
    st.markdown("#### All Engineers")
    display = pivot.copy()
    for c in kpi_cols:
        if c.strip().startswith("#"):
            display[c] = display[c].apply(lambda x: f"{x:.0f}" if pd.notna(x) else "—")
        else:
            display[c] = display[c].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    st.dataframe(display, use_container_width=True, hide_index=True)
