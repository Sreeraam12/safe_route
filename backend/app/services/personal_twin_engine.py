"""
SafeRoute Personal Digital Twin Engine
======================================
Implements individual user personalization, preference blending, segment memory,
and feedback-driven learning.

Conforms to SafeRoute Final Architecture Roadmap (Sections 24-37, 50-52).
"""

from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.user import PersonalPreferences
from backend.app.models.twin import PersonalTwinState, PersonalSegmentMemory
from backend.app.models.trip import Trip, TripFeedback


DEFAULT_TWIN_WEIGHTS = {
    "lighting_weight": 0.20,
    "crime_weight": 0.25,
    "isolation_weight": 0.20,
    "crowd_weight": 0.15,
    "traffic_weight": 0.10,
    "distance_weight": 0.10,
    "time_weight": 0.15,
    "night_weight": 0.20,
    "weather_weight": 0.05,
    "detour_tolerance": 0.25,
    "model_confidence": 0.10,
}


async def get_effective_twin_weights(
    user_id: Optional[int],
    db: AsyncSession,
) -> Dict[str, float]:
    """
    Get effective weights by blending user's explicit preferences with their
    learned Personal Twin state, governed by model confidence.
    """
    if not user_id:
        return DEFAULT_TWIN_WEIGHTS.copy()

    # Load explicit preferences
    pref_res = await db.execute(
        select(PersonalPreferences).where(PersonalPreferences.user_id == user_id)
    )
    prefs = pref_res.scalar_one_or_none()

    # Load learned Twin state
    twin_res = await db.execute(
        select(PersonalTwinState).where(PersonalTwinState.user_id == user_id)
    )
    twin = twin_res.scalar_one_or_none()

    if not prefs and not twin:
        return DEFAULT_TWIN_WEIGHTS.copy()

    confidence = twin.model_confidence if twin else 0.10
    explicit_weight = 1.0 - confidence
    learned_weight = confidence

    # Helper blend
    def blend(exp_val: Optional[float], lrn_val: Optional[float], default: float) -> float:
        e = exp_val if exp_val is not None else default
        l = lrn_val if lrn_val is not None else default
        return round(float(explicit_weight * e + learned_weight * l), 4)

    return {
        "lighting_weight": blend(prefs.lighting_preference if prefs else None, twin.lighting_weight if twin else None, 0.20),
        "crime_weight": blend(prefs.crime_sensitivity if prefs else None, twin.crime_weight if twin else None, 0.25),
        "isolation_weight": blend(prefs.isolation_aversion if prefs else None, twin.isolation_weight if twin else None, 0.20),
        "crowd_weight": blend(prefs.crowd_preference if prefs else None, twin.crowd_weight if twin else None, 0.15),
        "traffic_weight": blend(prefs.traffic_tolerance if prefs else None, twin.traffic_weight if twin else None, 0.10),
        "distance_weight": blend(prefs.distance_priority if prefs else None, twin.distance_weight if twin else None, 0.10),
        "time_weight": blend(prefs.time_priority if prefs else None, twin.time_weight if twin else None, 0.15),
        "night_weight": blend(prefs.night_safety_weight if prefs else None, twin.night_weight if twin else None, 0.20),
        "weather_weight": blend(prefs.weather_sensitivity if prefs else None, twin.weather_weight if twin else None, 0.05),
        "detour_tolerance": blend(prefs.detour_tolerance if prefs else None, twin.detour_tolerance if twin else None, 0.25),
        "model_confidence": round(float(confidence), 3),
    }


def calculate_personalized_route_risk(
    base_time_aware_risk: float,
    matched_segments_df: pd.DataFrame,
    twin_weights: Dict[str, float],
    time_context: Dict[str, Any],
    segment_memory_eval: Optional[Dict[str, Any]] = None,
) -> Dict[str, float]:
    """
    Apply Personal Twin adjustments to calculate Personalized Route Risk.

    Formula:
    Personalized Risk = Base Risk
                      + Lighting Adjustment
                      + Crime Sensitivity Adjustment
                      + Isolation Aversion Adjustment
                      + Crowd Preference Adjustment
                      + Night Adjustment
                      + Segment Memory Adjustment (road-level familiarity / avoidance)
    """
    total_length = matched_segments_df["edge_length"].sum() if "edge_length" in matched_segments_df.columns else 1.0
    if total_length <= 0:
        total_length = 1.0

    # 1. Lighting sensitivity adjustment
    lighting_adj = 0.0
    if "lighting_score" in matched_segments_df.columns:
        lighting = matched_segments_df["lighting_score"].fillna(50.0)
        poor_lighting_pct = np.clip((65.0 - lighting) / 65.0, 0.0, 1.0)
        avg_poor_lighting = (poor_lighting_pct * matched_segments_df.get("edge_length", 1.0)).sum() / total_length
        # Sensitivity relative to neutral 0.50
        lighting_scale = (twin_weights.get("lighting_weight", 0.5) - 0.5) * 2.0  # [-1.0, 1.0]
        mult = 1.5 if time_context.get("is_night") else 0.5
        lighting_adj = float(lighting_scale * avg_poor_lighting * 8.0 * mult)

    # 2. Isolation aversion adjustment
    isolation_adj = 0.0
    if "isolation_score" in matched_segments_df.columns:
        isolation = matched_segments_df["isolation_score"].fillna(30.0)
        avg_isolation = (isolation * matched_segments_df.get("edge_length", 1.0)).sum() / (total_length * 100.0)
        isolation_scale = (twin_weights.get("isolation_weight", 0.5) - 0.5) * 2.0
        isolation_adj = float(isolation_scale * avg_isolation * 10.0)

    # 3. Crime sensitivity adjustment
    crime_adj = 0.0
    if "crime_risk_100" in matched_segments_df.columns:
        crime_risk = matched_segments_df["crime_risk_100"].fillna(0.0)
        avg_crime = (crime_risk * matched_segments_df.get("edge_length", 1.0)).sum() / (total_length * 100.0)
        crime_scale = (twin_weights.get("crime_weight", 0.5) - 0.5) * 2.0
        crime_adj = float(crime_scale * avg_crime * 10.0)

    # 4. Night weight adjustment
    night_adj = 0.0
    if time_context.get("is_night"):
        night_scale = (twin_weights.get("night_weight", 0.5) - 0.5) * 2.0
        night_adj = float(night_scale * 5.0)

    # 5. Road-level segment memory adjustment
    seg_adj = 0.0
    familiar_count = 0
    avoided_count = 0
    if segment_memory_eval:
        seg_adj = segment_memory_eval.get("segment_memory_adjustment", 0.0)
        familiar_count = segment_memory_eval.get("familiar_segments_count", 0)
        avoided_count = segment_memory_eval.get("avoided_segments_count", 0)

    total_personal_adj = lighting_adj + isolation_adj + crime_adj + night_adj + seg_adj
    personalized_risk = float(np.clip(base_time_aware_risk + total_personal_adj, 0.0, 100.0))
    personalized_safety = float(100.0 - personalized_risk)

    return {
        "personalized_risk": round(personalized_risk, 2),
        "personalized_safety_score": round(personalized_safety, 2),
        "personal_adjustment": round(total_personal_adj, 2),
        "segment_memory_adjustment": round(seg_adj, 2),
        "familiar_segments_count": familiar_count,
        "avoided_segments_count": avoided_count,
        "lighting_adjustment": round(lighting_adj, 2),
        "isolation_adjustment": round(isolation_adj, 2),
        "crime_adjustment": round(crime_adj, 2),
    }


async def learn_from_trip_feedback(
    user_id: int,
    trip: Trip,
    feedback: TripFeedback,
    db: AsyncSession,
):
    """
    Bayesian-style update to the user's Personal Twin state following completed trip feedback.
    """
    twin_res = await db.execute(
        select(PersonalTwinState).where(PersonalTwinState.user_id == user_id)
    )
    twin = twin_res.scalar_one_or_none()
    if not twin:
        twin = PersonalTwinState(user_id=user_id, timestamp=datetime.utcnow())
        db.add(twin)

    learning_rate = 0.05

    # If user felt unsafe or reported low safety
    # 1. Safety & Danger Perception
    if feedback.felt_unsafe or feedback.safety_rating <= 2:
        twin.crime_weight = float(np.clip(twin.crime_weight + learning_rate * 1.5, 0.0, 1.0))
        twin.isolation_weight = float(np.clip(twin.isolation_weight + learning_rate * 1.5, 0.0, 1.0))
        twin.detour_tolerance = float(np.clip(twin.detour_tolerance + 0.05, 0.10, 0.50))
    elif feedback.safety_rating >= 4 and not feedback.felt_unsafe:
        twin.model_confidence = float(np.clip(twin.model_confidence + 0.04, 0.10, 0.95))

    # If user specifically complained about lighting
    if feedback.lighting_rating and feedback.lighting_rating <= 2:
        twin.lighting_weight = float(np.clip(twin.lighting_weight + learning_rate * 2.0, 0.0, 1.0))
    # 2. Lighting Quality Feedback
    if feedback.lighting_rating is not None:
        if feedback.lighting_rating <= 2:
            # Low lighting reported: increase priority on well-lit paths
            twin.lighting_weight = float(np.clip(twin.lighting_weight + learning_rate * 2.0, 0.0, 1.0))
            twin.night_weight = float(np.clip(twin.night_weight + learning_rate * 1.0, 0.0, 1.0))
        elif feedback.lighting_rating >= 4:
            # Satisfactory lighting
            twin.lighting_weight = float(np.clip(twin.lighting_weight - learning_rate * 0.5, 0.10, 1.0))

    # If user felt very safe and comfortable
    if feedback.safety_rating >= 4 and not feedback.felt_unsafe:
        twin.model_confidence = float(np.clip(twin.model_confidence + 0.03, 0.10, 0.95))
    else:
        twin.model_confidence = float(np.clip(twin.model_confidence + 0.02, 0.10, 0.95))
    # 3. Comfort & Road Surface Feedback
    if feedback.comfort_rating is not None:
        if feedback.comfort_rating <= 2:
            # Congested or rough corridor: increase traffic aversion and detour tolerance for smoother roads
            twin.traffic_weight = float(np.clip(twin.traffic_weight + learning_rate * 1.5, 0.0, 1.0))
            twin.detour_tolerance = float(np.clip(twin.detour_tolerance + 0.03, 0.10, 0.50))
        elif feedback.comfort_rating >= 4:
            # Comfortable ride
            twin.traffic_weight = float(np.clip(twin.traffic_weight - learning_rate * 0.5, 0.05, 1.0))

    # 4. Crowd & Bystander Activity Feedback
    if feedback.crowd_rating is not None:
        if feedback.crowd_rating <= 2:
            # Deserted/isolated street: increase crowd priority and isolation aversion
            twin.crowd_weight = float(np.clip(twin.crowd_weight + learning_rate * 1.8, 0.0, 1.0))
            twin.isolation_weight = float(np.clip(twin.isolation_weight + learning_rate * 1.2, 0.0, 1.0))
        elif feedback.crowd_rating >= 4:
            # Active and bustling street confirmed
            twin.crowd_weight = float(np.clip(twin.crowd_weight + learning_rate * 0.5, 0.0, 1.0))

    # 5. Navigation & Guidance Accuracy Feedback
    if feedback.navigation_rating is not None:
        if feedback.navigation_rating <= 2:
            # Complex/confusing turns: prioritize more direct routes
            twin.distance_weight = float(np.clip(twin.distance_weight + learning_rate * 1.0, 0.0, 1.0))
            twin.detour_tolerance = float(np.clip(twin.detour_tolerance - 0.03, 0.10, 0.50))

    # General confidence increase per validated trip
    twin.model_confidence = float(np.clip(twin.model_confidence + 0.02, 0.10, 0.95))

    twin.timestamp = datetime.utcnow()
    await db.commit()

