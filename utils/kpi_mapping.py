"""
Maps SAP Analytics Cloud column names to goals_app kpi_logic internal keys.
Also defines the template columns for the manual KPI upload.
"""

# All columns in the downloadable template (all KPIs needed for all 4 goals)
TEMPLATE_COLUMNS = [
    "Engineer",
    # Operational
    "IRT (%)", "APT (%)", "ORT (%)", "QMS (%)", "Infodoc (%)",
    "P1 Solved in 5 D (%)", "P2 Solved in 14 D (%)", "P1 Taken", "Total Incoming", "Completed Chats",
    # Customer
    "nCES (%)", "# Top 2 Box Surveys",
    # Innovation
    "KCS Focus (%)", "Pulse (%)", "Release Defects", "Innovation & Supportability",
    # People
    "# EA you started learning?", "# Gamification / Know Verse sessions?", "# R&R nominations & Participation in EE activities",
]

# Template column → kpi_logic key (all KPIs)
TEMPLATE_MAP = {
    "IRT (%)":                  "irt",
    "APT (%)":                  "apt",
    "ORT (%)":                  "ort",
    "QMS (%)":                  "qms",
    "Infodoc (%)":              "infodoc",
    "P1 Solved in 5 D (%)":     "p1_solved",
    "P2 Solved in 14 D (%)":    "p2_solved",
    "P1 Taken":                 "p1_taken",
    "Total Incoming":           "incoming",
    "Completed Chats":          "chat",
    "nCES (%)":                 "nces",
    "# Top 2 Box Surveys":      "surveys",
    "KCS Focus (%)":            "kcs_focus",
    "Pulse (%)":                "pulse",
    "Release Defects":          "release_defects",
    "Innovation & Supportability": "innovation_supportability",
    "# EA you started learning?":                                   "expert_area",
    "# Gamification / Know Verse sessions?":                        "gamification",
    "# R&R nominations & Participation in EE activities":           "swarms",
}
