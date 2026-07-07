import io
import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
from utils.parser import parse_report
from utils.kpi_mapping import TEMPLATE_COLUMNS

DATA_DIR = Path(__file__).parent.parent / "data"
LATEST_PATH = DATA_DIR / "last_report.xlsx"
SUPP_PATH   = DATA_DIR / "supplementary_kpis.xlsx"


def _all_saved_reports():
    if not DATA_DIR.exists():
        return []
    return sorted(DATA_DIR.glob("report_*.xlsx"), reverse=True)


def _make_template() -> bytes:
    df = pd.DataFrame(columns=TEMPLATE_COLUMNS)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


def show():
    st.markdown(
        """
        <div class="page-header">
            <h1>📁 Upload Report</h1>
            <p>Upload your SAP Analytics Cloud Excel report</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Upload SAP report ──────────────────────────────────────────────────────
    st.markdown("#### 1 · Upload SAP Report")
    uploaded = st.file_uploader("Select SAP Analytics Cloud Excel file", type=["xlsx"], key="sap_upload")

    if uploaded:
        try:
            DATA_DIR.mkdir(exist_ok=True)
            dated_path = DATA_DIR / f"report_{date.today().strftime('%Y_%m_%d')}.xlsx"
            with open(dated_path, "wb") as f:
                f.write(uploaded.getbuffer())
            with open(LATEST_PATH, "wb") as f:
                f.write(uploaded.getbuffer())
            parsed = parse_report(dated_path)
            st.session_state["parsed"] = parsed
            st.session_state["active_report"] = dated_path.name
            st.success(
                f"✅ Saved as **{dated_path.name}** — "
                f"**{len(parsed['kpis'])} KPIs**, "
                f"**{parsed['data']['Engineer'].nunique()} engineers**, "
                f"**{len(parsed['periods'])} periods**"
            )
        except Exception as e:
            st.error(f"Could not parse the file: {e}")
            return

    st.markdown("---")

    # ── KPI template + upload ──────────────────────────────────────────────────
    st.markdown("#### 2 · Download & Upload KPI Data Template")
    st.caption(
        "Download the template, fill one row per engineer with all KPI values for all 4 goals, then upload."
    )

    st.download_button(
        label="⬇️ Download KPI Template",
        data=_make_template(),
        file_name="kpi_template_v2.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    supp_file = st.file_uploader("Upload filled KPI template", type=["xlsx"], key="supp_upload")
    if supp_file:
        try:
            DATA_DIR.mkdir(exist_ok=True)
            with open(SUPP_PATH, "wb") as f:
                f.write(supp_file.getbuffer())
            supp_df = pd.read_excel(SUPP_PATH)
            supp_df.columns = [c.strip() for c in supp_df.columns]
            st.session_state["supp_data"] = supp_df
            st.success(f"✅ Supplementary KPIs loaded — **{len(supp_df)} engineers**")
        except Exception as e:
            st.error(f"Could not load supplementary file: {e}")

    # Auto-load saved supplementary file
    if "supp_data" not in st.session_state and SUPP_PATH.exists():
        try:
            supp_df = pd.read_excel(SUPP_PATH)
            supp_df.columns = [c.strip() for c in supp_df.columns]
            st.session_state["supp_data"] = supp_df
        except Exception:
            pass

    if "supp_data" in st.session_state:
        st.caption(f"Supplementary KPIs loaded for **{len(st.session_state['supp_data'])} engineers**")

    st.markdown("---")

    # ── Load from saved reports ────────────────────────────────────────────────
    st.markdown("#### Load a Saved Report")
    saved = _all_saved_reports()

    if not saved:
        st.info("No saved reports yet. Upload a file above.")
        return

    report_names = [f.name for f in saved]
    active = st.session_state.get("active_report", report_names[0])
    active_idx = report_names.index(active) if active in report_names else 0

    selected = st.selectbox("Select report to load", options=report_names, index=active_idx)

    if st.button("📂 Load Selected Report", use_container_width=True):
        try:
            selected_path = DATA_DIR / selected
            parsed = parse_report(selected_path)
            st.session_state["parsed"] = parsed
            st.session_state["active_report"] = selected
            st.success(f"✅ Loaded **{selected}**")
        except Exception as e:
            st.error(f"Could not load report: {e}")

    if "active_report" in st.session_state:
        st.caption(f"Currently loaded: **{st.session_state['active_report']}**")

    st.markdown("---")

    # ── Delete a saved report ──────────────────────────────────────────────────
    st.markdown("#### Delete a Saved Report")
    del_selected = st.selectbox("Select report to delete", options=report_names, key="del_report")

    if st.button("🗑️ Delete Selected Report", type="primary", use_container_width=True):
        del_path = DATA_DIR / del_selected
        if del_path.exists():
            del_path.unlink()
            if st.session_state.get("active_report") == del_selected:
                st.session_state.pop("parsed", None)
                st.session_state.pop("active_report", None)
            st.success(f"✅ Deleted **{del_selected}**")
            st.rerun()
        else:
            st.error("File not found.")
