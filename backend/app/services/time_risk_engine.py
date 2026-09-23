"""
SafeRoute Time-Aware Risk Engine
================================
Provides dynamic contextual time-risk calculations based on departure datetime,
fuzzy temporal vulnerability curves (morning, afternoon, evening transition,
night, late-night), and time-environment interaction penalties (lighting,
isolation, crowd).

Conforms to SafeRoute Final Architecture Roadmap (Sections 17-21).
"""

import math
from datetime import datetime
from typing import Dict, Any
import numpy as np
import pandas as pd


def calculate_time_context(travel_datetime: datetime) -> Dict[str, Any]:
    """
    Build standardized time features and temporal vulnerability metrics
    for a given departure datetime.
    """
    hour = travel_datetime.hour
    minute = travel_datetime.minute
    float_hour = hour + minute / 60.0
    day_of_week = travel_datetime.weekday()
    is_weekend = int(day_of_week >= 5)

    # Standardized is_night: hour < 6 or hour >= 18
    is_night = int(hour < 6 or hour >= 18)

    hour_sin = math.sin(2.0 * math.pi * float_hour / 24.0)
    hour_cos = math.cos(2.0 * math.pi * float_hour / 24.0)

    # Fuzzy temporal period memberships and base vulnerability
    # ---------------------------------------------------------
    # 06:00 - 12:00: Morning (daylight, active commute, lowest baseline risk)
    # 12:00 - 17:00: Afternoon (daylight, commercial activity)
    # 17:00 - 20:00: Evening transition (dusk, fading daylight)
    # 20:00 - 23:00: Night (darkness, reduced bystander density)
    # 23:00 - 05:00: Late Night (isolated streets, maximum vulnerability)

    if 6.0 <= float_hour < 12.0:
        period = "morning"
        # 15.0 at 9am, smoothly interpolating
        base_time_risk = 15.0 + 5.0 * (1.0 - math.sin(math.pi * (float_hour - 6.0) / 6.0))
    elif 12.0 <= float_hour < 17.0:
        period = "afternoon"
        base_time_risk = 20.0 + 5.0 * ((float_hour - 12.0) / 5.0)
    elif 17.0 <= float_hour < 20.0:
        period = "evening"
        # Rising from 25.0 to 55.0 as daylight disappears
        progress = (float_hour - 17.0) / 3.0
        base_time_risk = 25.0 + progress * 30.0
    elif 20.0 <= float_hour < 23.0:
        period = "night"
        # Rising from 55.0 to 75.0
        progress = (float_hour - 20.0) / 3.0
        base_time_risk = 55.0 + progress * 20.0
    else:
        period = "late_night"
        # 23:00 to 05:59: Peak risk between 75.0 and 85.0
        if float_hour >= 23.0:
            progress = (float_hour - 23.0) / 1.0
        else:
            progress = (float_hour + 1.0) / 7.0
        base_time_risk = 75.0 + min(10.0, progress * 10.0)

    # Weekend late-night penalty (+5 if midnight on weekend)
    if is_weekend and (float_hour >= 22.0 or float_hour < 5.0):
        base_time_risk += 5.0

    base_time_risk = max(0.0, min(100.0, base_time_risk))

    return {
        "travel_datetime": travel_datetime,
        "hour": hour,
        "minute": minute,
        "float_hour": round(float_hour, 2),
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "is_night": is_night,
        "hour_sin": round(hour_sin, 4),
        "hour_cos": round(hour_cos, 4),
        "period": period,
        "base_time_risk": round(base_time_risk, 2),
    }


def compute_time_aware_segment_risk(
    segment_df: pd.DataFrame,
    time_context: Dict[str, Any],
) -> pd.Series:
    """
    Adjust segment hybrid risk based on departure time and environmental interaction.

    Contextual penalties:
    1. Poor lighting penalty is amplified at night (is_night == 1).
    2. Isolation penalty is amplified during late-night and night periods.
    3. Low crowd penalty is elevated during off-peak and night hours.
    4. Base temporal risk modulates the baseline.
    """
    base_hybrid = segment_df["hybrid_risk_100"].copy()
    base_time_risk = time_context["base_time_risk"]
    is_night = time_context["is_night"]
    period = time_context["period"]

    # 1. Base blend: 80% base road infrastructure/crime + 20% temporal curve
    combined_risk = 0.80 * base_hybrid + 0.20 * base_time_risk

    # 2. Contextual Lighting Interaction:
    # If lighting_score exists (0=pitch dark, 100=well lit)
    if "lighting_score" in segment_df.columns:
        lighting = segment_df["lighting_score"].fillna(50.0)
        poor_lighting_factor = np.clip((70.0 - lighting) / 70.0, 0.0, 1.0)
        # Lighting deficit matters primarily when it is dark
        if is_night:
            combined_risk += poor_lighting_factor * 8.0  # up to +8 risk for dark streets
        elif period == "evening":
            combined_risk += poor_lighting_factor * 4.0

    # 3. Contextual Isolation Interaction:
    # If isolation_score exists (0=busy/open, 100=highly isolated)
    if "isolation_score" in segment_df.columns:
        isolation = segment_df["isolation_score"].fillna(30.0)
        isolation_factor = np.clip(isolation / 100.0, 0.0, 1.0)
        if period == "late_night":
            combined_risk += isolation_factor * 7.0  # isolated street at 2am is dangerous
        elif period == "night":
            combined_risk += isolation_factor * 4.0

    # 4. Contextual Crowd Interaction:
    # If crowd_score exists (0=deserted, 100=lively)
    if "crowd_score" in segment_df.columns:
        crowd = segment_df["crowd_score"].fillna(50.0)
        deserted_factor = np.clip((50.0 - crowd) / 50.0, 0.0, 1.0)
        if is_night:
            combined_risk += deserted_factor * 5.0

    return combined_risk.clip(0.0, 100.0)

