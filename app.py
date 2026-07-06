import streamlit as st
from pathlib import Path
from utils.parser import parse_report

SAVED_REPORT_PATH = Path(__file__).parent / "data" / "last_report.xlsx"

# Auto-load saved report on every startup
if "parsed" not in st.session_state and SAVED_REPORT_PATH.exists():
    try:
        with open(SAVED_REPORT_PATH, "rb") as f:
            st.session_state["parsed"] = parse_report(f)
    except Exception:
        pass

st.set_page_config(
    page_title="Team Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background-color: #f0f4f8; }
    [data-testid="stMain"] { background-color: #f0f4f8; }
    [data-testid="stHeader"] { background-color: #1a1f36 !important; }
    [data-testid="stHeader"] * { color: #ffffff !important; fill: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #1a1f36; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] button {
        background-color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] button p {
        color: #1a1f36 !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] button:hover { background-color: #e2e8f0 !important; }
    .page-header {
        padding: 0.2rem 0 0.4rem 0;
        border-bottom: 2px solid #cbd5e1;
        margin-bottom: 1.5rem;
    }
    .page-header h1 { font-size: 1.8rem; font-weight: 700; color: #1a1f36; margin: 0; }
    .page-header p { color: #64748b; margin: 0.2rem 0 0 0; }
    [data-testid="stMain"] p,
    [data-testid="stMain"] label,
    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3 { color: #1a1f36 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        <div style="padding:0.8rem 0 1rem 0;border-bottom:1px solid #3d4475;margin-bottom:0.5rem;">
            <p style="font-size:0.65rem;color:#94a3b8;text-transform:uppercase;
            letter-spacing:0.08em;margin:0;">📊 Tool</p>
            <p style="font-size:1rem;font-weight:700;color:#ffffff;margin:0;">Team Dashboard</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "page" not in st.session_state:
        st.session_state.page = "Upload"

    if st.button("📁  Upload Report", use_container_width=True):
        st.session_state.page = "Upload"
    if st.button("📊  Team Summary", use_container_width=True):
        st.session_state.page = "Team Summary"
    if st.button("🏆  Engineer Ranking", use_container_width=True):
        st.session_state.page = "Ranking"
    if st.button("🎯  Goal Ratings", use_container_width=True):
        st.session_state.page = "Goal Ratings"

    st.markdown("---")
    st.caption("Team Dashboard v0.1")

if st.session_state.page == "Upload":
    from views.upload import show
    show()
elif st.session_state.page == "Team Summary":
    from views.team_summary import show
    show()
elif st.session_state.page == "Ranking":
    from views.ranking import show
    show()
elif st.session_state.page == "Goal Ratings":
    from views.goal_ratings import show
    show()
