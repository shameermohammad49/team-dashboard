"""
Rating scale: 1 (below threshold), 2, 3, 4 (best).
Each KPI has a direction: "higher_is_better" or "lower_is_better".
Thresholds define the lower bounds for ratings 2, 3, and 4.
Values below the rating-2 threshold get rating 1.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class KPIDefinition:
    label: str
    unit: str
    direction: Literal["higher_is_better", "lower_is_better"]
    # (min_value_inclusive, rating) pairs, checked in descending rating order
    thresholds: list  # [(threshold, rating), ...]


# Thresholds derived from user spec:
#   2 = <lower, 3 = mid range, 4 = >upper
# "higher_is_better" KPIs: value >= threshold → rating
OPERATIONAL_KPIS: dict[str, KPIDefinition] = {
    "irt": KPIDefinition(
        label="IRT",
        unit="%",
        direction="higher_is_better",
        thresholds=[(97, 4), (95, 3), (0, 2)],
    ),
    "apt": KPIDefinition(
        label="APT",
        unit="%",
        direction="higher_is_better",
        thresholds=[(97, 4), (95, 3), (0, 2)],
    ),
    "ort": KPIDefinition(
        label="ORT",
        unit="%",
        direction="higher_is_better",
        thresholds=[(96, 4), (95, 3), (0, 2)],
    ),
    "qms": KPIDefinition(
        label="QMS",
        unit="%",
        direction="higher_is_better",
        thresholds=[(97, 4), (95, 3), (0, 2)],
    ),
    "chat": KPIDefinition(
        label="Chat",
        unit="",
        direction="higher_is_better",
        thresholds=[(28, 4), (22, 3), (0, 2)],
    ),
    "incoming": KPIDefinition(
        label="Incoming",
        unit="",
        direction="higher_is_better",
        thresholds=[(370, 4), (270, 3), (0, 2)],
    ),
    "p1_solved": KPIDefinition(
        label="P1 Solved",
        unit="%",
        direction="higher_is_better",
        thresholds=[(80, 4), (75, 3), (0, 2)],
    ),
    "p2_solved": KPIDefinition(
        label="P2 Solved",
        unit="%",
        direction="higher_is_better",
        thresholds=[(80, 4), (70, 3), (0, 2)],
    ),
    "p1_taken": KPIDefinition(
        label="P1 Taken",
        unit="",
        direction="higher_is_better",
        thresholds=[(32, 4), (26, 3), (0, 2)],
    ),
}


CUSTOMER_KPIS: dict[str, KPIDefinition] = {
    "nces": KPIDefinition(
        label="nCES",
        unit="%",
        direction="higher_is_better",
        thresholds=[(83.49, 4), (81.5, 3), (0, 2)],
    ),
    "surveys": KPIDefinition(
        label="# Top 2 Box Surveys",
        unit="",
        direction="higher_is_better",
        thresholds=[(90, 4), (60, 3), (0, 2)],
    ),
}


def _rate_from_definition(kpi: KPIDefinition, value: float) -> int:
    for threshold, rating in kpi.thresholds:
        if value >= threshold:
            return rating
    return 1


def calculate_rating(key: str, value: float | None) -> int | None:
    """Return 1-4 rating for an Operational KPI value, or None if value is None."""
    if value is None:
        return None
    return _rate_from_definition(OPERATIONAL_KPIS[key], value)


def calculate_customer_kpi_rating(key: str, value: float | None) -> int | None:
    """Return 1-4 rating for a Customer KPI value, or None if value is None."""
    if value is None:
        return None
    return _rate_from_definition(CUSTOMER_KPIS[key], value)


RATING_COLORS = {
    1: ("#fff1f0", "#cf1322"),  # bg, text
    2: ("#fff7e6", "#d46b08"),
    3: ("#f0f9ff", "#0369a1"),
    4: ("#f0fdf4", "#15803d"),
}

RATING_LABELS = {1: "Does Not Meet Expectations", 2: "Partially Meets Expectations", 3: "Meets Expectations", 4: "Exceeds Expectations"}

GOAL_RATING_COLORS = {
    1: ("#fff1f0", "#cf1322"),
    2: ("#fff7e6", "#d46b08"),
    3: ("#f0f9ff", "#0369a1"),
    4: ("#f0fdf4", "#15803d"),
    5: ("#f5f3ff", "#6d28d9"),
}

GOAL_RATING_LABELS = {
    1: "Does Not Meet Expectations",
    2: "Partially Meets Expectations",
    3: "Meets Expectations",
    4: "Exceeds Expectations",
    5: "Consistently Exceeds Expectations",
}

# KPIs that cannot be rated 2 when the overall goal is Rating 4
_PROTECTED_FROM_2 = {"ort", "incoming"}


def calculate_operational_goal_rating(kpi_values: dict) -> int | None:
    """
    Return overall Operational Goal rating (1–5).
    Returns None if any KPI value is missing.

    Rules:
      5 — all 9 KPIs rated 4
      4 — majority 4s, rest 3s (no 2s)
      4 — majority 4s, exactly one 2 (not ORT/Incoming), remaining 3s
      3 — majority 4s, one 2 that IS ORT or Incoming, remaining 3s
      3 — majority 4s, more than one 2 (any combination with 3s)
      3 — equal count of 4s and 3s
      3 — majority 3s
      2 — majority 2s
      1 — everything else
    """
    rated = {}
    for key in OPERATIONAL_KPIS:
        r = calculate_rating(key, kpi_values.get(key))
        if r is None:
            return None
        rated[key] = r

    ratings = list(rated.values())
    total = len(ratings)
    majority = total // 2 + 1  # 5 out of 9

    counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for r in ratings:
        counts[r] += 1

    # Special rule: Incoming < 330 (but still rated 3) blocks Rating 4
    incoming_val = kpi_values.get("incoming")
    incoming_blocks_4 = incoming_val is not None and incoming_val < 330

    if counts[4] == total:
        return 5

    twos = [k for k, r in rated.items() if r == 2]

    if counts[1] == 0:
        # Rating 4: majority 4s, no 2s (rest all 3s)
        if counts[4] >= majority and len(twos) == 0 and not incoming_blocks_4:
            return 4

        # Rating 4: majority 4s, exactly one non-protected 2, rest 3s
        if counts[4] >= majority and len(twos) == 1 and twos[0] not in _PROTECTED_FROM_2 and not incoming_blocks_4:
            return 4

        # Rating 4: majority 4s, exactly two 2s, both non-protected, rest 3s
        if counts[4] >= majority and len(twos) == 2 and all(k not in _PROTECTED_FROM_2 for k in twos) and not incoming_blocks_4:
            return 4

        # Rating 3: majority 4s with any 2s (protected or multiple)
        if counts[4] >= majority:
            return 3

        # Rating 3: 4 or more 4s but 2s outnumber or equal 4s (not dominant)
        if counts[4] >= 4 and counts[2] >= counts[4]:
            return 3

        # Rating 3: exactly 4 fours (not majority), 3s+4s outnumber 2s
        if counts[4] == 4 and (counts[4] + counts[3]) > counts[2]:
            return 3

        # Rating 3: equal count of 4s and 3s
        if counts[4] == counts[3] and counts[4] > 0:
            return 3

        # Rating 3: majority 3s
        if counts[3] >= majority:
            return 3

        # Rating 3: 4 or more 3s (significant presence even if not majority)
        if counts[3] >= 4:
            return 3

    # Rating 2: 2s are more than any other single rating
    if counts[2] > counts[4] and counts[2] > counts[3] and counts[2] > counts[1]:
        return 2

    return 1


def calculate_customer_goal_rating(kpi_values: dict) -> int | None:
    """
    Return overall Customer Goal rating (1–5).
    Returns None if any KPI value is missing.

    Rules:
      5 — both rated 4 AND nCES >= 85 AND Surveys >= 100
      4 — both rated 4 but nCES < 85 OR Surveys < 100
      4 — nCES rated 4, Surveys rated 3
      3 — nCES rated 4, Surveys rated 2
      3 — nCES rated 3, Surveys rated 4
      3 — nCES rated 3, Surveys rated 2
      3 — both rated 3
      2 — nCES rated 2, Surveys rated 3
      2 — nCES rated 2, Surveys rated 4
      2 — both rated 2 AND nCES >= 70 AND Surveys >= 40
      1 — everything else
    """
    ratings = {}
    for key in CUSTOMER_KPIS:
        r = calculate_customer_kpi_rating(key, kpi_values.get(key))
        if r is None:
            return None
        ratings[key] = r

    nces_r    = ratings.get("nces")
    surveys_r = ratings.get("surveys")
    nces_val  = kpi_values.get("nces") or 0
    surv_val  = kpi_values.get("surveys") or 0

    # Rating 5: both 4 AND nCES >= 85 AND Surveys >= 100
    if nces_r == 4 and surveys_r == 4 and nces_val >= 85 and surv_val >= 100:
        return 5

    # Rating 4: both 4 but conditions for 5 not met
    if nces_r == 4 and surveys_r == 4:
        return 4

    # Rating 4: nCES 4, Surveys 3
    if nces_r == 4 and surveys_r == 3:
        return 4

    # Rating 3: nCES 4, Surveys 2
    if nces_r == 4 and surveys_r == 2:
        return 3

    # Rating 3: nCES 3, Surveys 4
    if nces_r == 3 and surveys_r == 4:
        return 3

    # Rating 3: nCES 3, Surveys 2
    if nces_r == 3 and surveys_r == 2:
        return 3

    # Rating 3: both 3
    if nces_r == 3 and surveys_r == 3:
        return 3

    # Rating 2: nCES 2, Surveys 3
    if nces_r == 2 and surveys_r == 3:
        return 2

    # Rating 2: nCES 2, Surveys 4
    if nces_r == 2 and surveys_r == 4:
        return 2

    # Rating 2: both 2 AND nCES >= 70 AND Surveys >= 40
    if nces_r == 2 and surveys_r == 2 and nces_val >= 70 and surv_val >= 40:
        return 2

    return 1
    return 1


INNOVATION_KPIS: dict[str, KPIDefinition] = {
    "kcs_focus": KPIDefinition(
        label="KCS Focus",
        unit="%",
        direction="higher_is_better",
        thresholds=[(10, 4), (8, 3), (0, 2)],
    ),
    "pulse": KPIDefinition(
        label="Pulse",
        unit="%",
        direction="higher_is_better",
        thresholds=[(85, 4), (75, 3), (0, 2)],
    ),
    "release_defects": KPIDefinition(
        label="Release Defects",
        unit="",
        direction="higher_is_better",
        thresholds=[(4, 4), (2, 3), (0, 2)],
    ),
    "innovation_supportability": KPIDefinition(
        label="Innovation & Supportability",
        unit="count",
        direction="higher_is_better",
        thresholds=[(4, 4), (2, 3), (0, 2)],
    ),
}


def calculate_innovation_kpi_rating(key: str, value: float | None) -> int | None:
    if value is None:
        return None
    return _rate_from_definition(INNOVATION_KPIS[key], value)


def calculate_innovation_goal_rating(kpi_values: dict) -> int | None:
    """
    Return overall Innovation Goal rating (1–5).
    Returns None if any KPI value is missing.

    Rules:
      5 — all KPIs rated 4
      4 — majority rated 4, rest 2s or 3s
      3 — all 3s, OR majority 3s with rest 2s or 4s
      2 — all 2s, OR majority 2s with rest 3s or 4s
      1 — everything else
    """
    rated = {}
    for key in INNOVATION_KPIS:
        r = calculate_innovation_kpi_rating(key, kpi_values.get(key))
        if r is None:
            return None
        rated[key] = r

    ratings = list(rated.values())
    total = len(ratings)
    majority = total // 2 + 1  # 3 out of 4

    counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for r in ratings:
        counts[r] += 1

    # Rating 5: all rated 4
    if counts[4] == total:
        return 5

    # Rating 4: majority 4s, rest are 2s or 3s (no 1s)
    if counts[1] == 0 and counts[4] >= majority:
        return 4

    # Rating 4: exactly 2 fours, rest are mix of 2s and 3s (no 1s), 4s dominate
    if counts[1] == 0 and counts[4] == 2 and counts[4] >= counts[3] and counts[4] >= counts[2]:
        return 4

    # Rating 4: exactly 2 fours, 2 twos (tie → Rating 4)
    if counts[1] == 0 and counts[4] == 2 and counts[2] == 2 and counts[3] == 0:
        return 4

    # Rating 3: all 3s
    if counts[3] == total:
        return 3

    # Rating 3: majority 3s, rest 2s or 4s (no 1s)
    if counts[1] == 0 and counts[3] >= majority:
        return 3

    # Rating 3: 3s and 4s together form majority, at least one 3 (no 1s)
    if counts[1] == 0 and counts[3] >= 1 and (counts[3] + counts[4]) >= majority:
        return 3

    # Rating 3: 1 four, 1 three, 2 twos
    if counts[1] == 0 and counts[4] == 1 and counts[3] == 1 and counts[2] == 2:
        return 3

    # Rating 3: 2 threes, 2 twos
    if counts[1] == 0 and counts[3] == 2 and counts[2] == 2 and counts[4] == 0:
        return 3

    # Rating 2: all 2s
    if counts[2] == total:
        return 2

    # Rating 2: majority 2s, rest 3s or 4s (no 1s)
    if counts[1] == 0 and counts[2] >= majority:
        return 2

    # Rating 2: exactly 2 twos, rest are mix of 3s and 4s (no 1s), 2s dominate
    if counts[1] == 0 and counts[2] == 2 and counts[2] >= counts[3] and counts[2] >= counts[4]:
        return 2

    return 1


PEOPLE_KPIS: dict[str, KPIDefinition] = {
    "expert_area": KPIDefinition(
        label="# EA you started learning?",
        unit="count",
        direction="higher_is_better",
        thresholds=[(2, 4), (1, 3), (0, 2)],
    ),
    "gamification": KPIDefinition(
        label="# Gamification / Know Verse sessions?",
        unit="count",
        direction="higher_is_better",
        thresholds=[(2, 4), (1, 3), (0, 2)],
    ),
    "swarms": KPIDefinition(
        label="# R&R nominations & Participation in EE activities",
        unit="count",
        direction="higher_is_better",
        thresholds=[(3, 4), (2, 3), (1, 2)],
    ),
}


def calculate_people_kpi_rating(key: str, value: float | None) -> int | None:
    if value is None:
        return None
    return _rate_from_definition(PEOPLE_KPIS[key], value)


def calculate_people_goal_rating(kpi_values: dict) -> int | None:
    """
    Return overall People Goal rating (1–5).
    Returns None if any KPI value is missing.

    Rules:
      5 — all 3 KPIs rated 4
      4 — two 4s (and one anything)
      4 — EA is the only 4, rest any
      3 — EA is the only 3, rest 2s
      3 — two 3s and rest 2s
      3 — all 3s
      2 — all 2s
      1 — everything else
    """
    rated = {}
    for key in PEOPLE_KPIS:
        r = calculate_people_kpi_rating(key, kpi_values.get(key))
        if r is None:
            return None
        rated[key] = r

    ea_r   = rated.get("expert_area")
    gam_r  = rated.get("gamification")
    rnr_r  = rated.get("swarms")

    ratings = [ea_r, gam_r, rnr_r]
    counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for r in ratings:
        counts[r] += 1

    # Rating 5: all 3 rated 4
    if counts[4] == 3:
        return 5

    # Rating 4: two or more 4s
    if counts[4] >= 2:
        return 4

    # Rating 4: EA is the only 4
    if ea_r == 4 and counts[4] == 1:
        return 4

    # Rating 3: one 4 (not EA) and two 3s
    if counts[4] == 1 and ea_r != 4 and counts[3] == 2:
        return 3

    # Rating 3: EA is the only 3, rest are 2s
    if ea_r == 3 and gam_r == 2 and rnr_r == 2:
        return 3

    # Rating 3: two 3s and rest 2s
    if counts[3] == 2 and counts[2] == 1:
        return 3

    # Rating 3: all 3s
    if counts[3] == 3:
        return 3

    # Rating 2: all 2s
    if counts[2] == 3:
        return 2

    return 1
