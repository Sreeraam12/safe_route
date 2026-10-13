"""
SafeRoute Personal Segment Memory Service
=========================================
Implements road-segment-level familiarity, trust memory, implicit choice learning
(selection vs rejection), and post-trip traversal feedback.

Conforms to SafeRoute Final Architecture Roadmap (Sections 32 & 49-52)
and Personal Digital Twin road-memory specifications.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.twin import PersonalSegmentMemory


def _recalculate_memory_metrics(mem: PersonalSegmentMemory):
    """
    Recalculates continuous trust score, avoidance score, confidence,
    and personal risk adjustment for a segment memory record.
    """
    visits = max(0, mem.visit_count or 0)
    selections = max(0, mem.selection_count or 0)
    rejections = max(0, mem.rejection_count or 0)
    pos_feed = max(0, mem.positive_feedback_count or 0)
    neg_feed = max(0, mem.negative_feedback_count or 0)

    total_evidence = visits + selections + rejections + pos_feed + neg_feed
    if total_evidence == 0:
        mem.trust_score = 0.5
        mem.avoidance_score = 0.0
        mem.confidence = 0.0
        mem.personal_risk_adjustment = 0.0
        return

    # Confidence grows with cumulative interactions (saturates near 8-10 interactions)
    mem.confidence = round(float(np.clip(total_evidence / 8.0, 0.05, 0.95)), 3)

    # Positive evidence (visits + selections + good feedback)
    pos_weight = 1.6 * pos_feed + 0.8 * visits + 0.4 * selections
    # Negative evidence (rejections + bad feedback)
    neg_weight = 2.5 * neg_feed + 0.6 * rejections

    denom = visits + selections + rejections + 1.0

    mem.trust_score = round(float(np.clip(pos_weight / denom, 0.0, 1.0)), 3)
    mem.avoidance_score = round(float(np.clip(neg_weight / denom, 0.0, 1.0)), 3)

    # Personal risk adjustment delta in [-15.0, +25.0]
    # Trusted familiar roads get a safety bonus (negative risk)
    # Avoided or trauma roads get a risk penalty (positive risk)
    trust_bonus = -15.0 * mem.trust_score * mem.confidence
    avoid_penalty = 25.0 * mem.avoidance_score * mem.confidence

    mem.personal_risk_adjustment = round(float(np.clip(trust_bonus + avoid_penalty, -15.0, 25.0)), 2)


async def record_route_selection_and_rejections(
    user_id: Optional[int],
    selected_segments: List[str],
    candidate_routes_segments: List[List[str]],
    db: AsyncSession,
) -> None:
    """
    Records implicit choice signals:
    - Segments in the selected route receive selection_count += 1
    - Segments offered in other candidate routes but NOT chosen receive rejection_count += 1
    """
    if not user_id:
        return

    selected_set: Set[str] = set(selected_segments)
    all_candidate_set: Set[str] = set()
    for route_segs in candidate_routes_segments:
        all_candidate_set.update(route_segs)

    # Rejected segments are those presented in other routes but not included in selected route
    rejected_set: Set[str] = all_candidate_set - selected_set
    all_relevant = list(selected_set | rejected_set)
    if not all_relevant:
        return

    # Load existing memories in one query
    res = await db.execute(
        select(PersonalSegmentMemory).where(
            PersonalSegmentMemory.user_id == user_id,
            PersonalSegmentMemory.osm_segment_id.in_(all_relevant),
        )
    )
    existing_map = {m.osm_segment_id: m for m in res.scalars().all()}

    # Update selected
    for seg_id in selected_set:
        if not seg_id:
            continue
        mem = existing_map.get(seg_id)
        if not mem:
            mem = PersonalSegmentMemory(
                user_id=user_id,
                osm_segment_id=str(seg_id),
                visit_count=0,
                selection_count=1,
                rejection_count=0,
            )
            db.add(mem)
            existing_map[seg_id] = mem
        else:
            mem.selection_count += 1

        _recalculate_memory_metrics(mem)

    # Update rejected
    for seg_id in rejected_set:
        if not seg_id:
            continue
        mem = existing_map.get(seg_id)
        if not mem:
            mem = PersonalSegmentMemory(
                user_id=user_id,
                osm_segment_id=str(seg_id),
                visit_count=0,
                selection_count=0,
                rejection_count=1,
            )
            db.add(mem)
            existing_map[seg_id] = mem
        else:
            mem.rejection_count += 1

        _recalculate_memory_metrics(mem)

    await db.commit()


async def record_trip_traversal(
    user_id: Optional[int],
    traversed_segments: List[str],
    db: AsyncSession,
) -> None:
    """
    Increments visit_count and updates last_visit for all traversed segments.
    """
    if not user_id or not traversed_segments:
        return

    unique_segs = list(set(traversed_segments))
    res = await db.execute(
        select(PersonalSegmentMemory).where(
            PersonalSegmentMemory.user_id == user_id,
            PersonalSegmentMemory.osm_segment_id.in_(unique_segs),
        )
    )
    existing_map = {m.osm_segment_id: m for m in res.scalars().all()}
    now = datetime.utcnow()

    for seg_id in unique_segs:
        if not seg_id:
            continue
        mem = existing_map.get(seg_id)
        if not mem:
            mem = PersonalSegmentMemory(
                user_id=user_id,
                osm_segment_id=str(seg_id),
                visit_count=1,
                selection_count=1,
                rejection_count=0,
                last_visit=now,
            )
            db.add(mem)
            existing_map[seg_id] = mem
        else:
            mem.visit_count = (mem.visit_count or 0) + 1
            mem.last_visit = now

        _recalculate_memory_metrics(mem)

    await db.commit()


async def record_trip_feedback_on_segments(
    user_id: Optional[int],
    traversed_segments: List[str],
    felt_unsafe: bool,
    safety_rating: int,
    incident_reported: bool,
    db: AsyncSession,
) -> None:
    """
    Updates positive or negative feedback counts on traversed segments based on user's post-trip rating.
    """
    if not user_id or not traversed_segments:
        return

    unique_segs = list(set(traversed_segments))
    res = await db.execute(
        select(PersonalSegmentMemory).where(
            PersonalSegmentMemory.user_id == user_id,
            PersonalSegmentMemory.osm_segment_id.in_(unique_segs),
        )
    )
    existing_map = {m.osm_segment_id: m for m in res.scalars().all()}

    is_negative = felt_unsafe or (safety_rating <= 2) or incident_reported
    is_positive = (safety_rating >= 4) and not felt_unsafe

    for seg_id in unique_segs:
        if not seg_id:
            continue
        mem = existing_map.get(seg_id)
        if not mem:
            mem = PersonalSegmentMemory(
                user_id=user_id,
                osm_segment_id=str(seg_id),
                visit_count=1,
                selection_count=1,
                rejection_count=0,
                positive_feedback_count=1 if is_positive else 0,
                negative_feedback_count=1 if is_negative else 0,
                last_visit=datetime.utcnow(),
            )
            db.add(mem)
            existing_map[seg_id] = mem
        else:
            mem.visit_count = (mem.visit_count or 0) + 1
            mem.last_visit = datetime.utcnow()
            if is_positive:
                mem.positive_feedback_count = (mem.positive_feedback_count or 0) + 1
            elif is_negative:
                mem.negative_feedback_count = (mem.negative_feedback_count or 0) + 1

        _recalculate_memory_metrics(mem)

    await db.commit()


async def record_segment_unsafe_incident(
    user_id: Optional[int],
    osm_segment_id: str,
    db: AsyncSession,
) -> None:
    """
    Direct penalty when user explicitly marks a corridor unsafe or triggers SOS.
    """
    if not user_id or not osm_segment_id:
        return

    res = await db.execute(
        select(PersonalSegmentMemory).where(
            PersonalSegmentMemory.user_id == user_id,
            PersonalSegmentMemory.osm_segment_id == osm_segment_id,
        )
    )
    mem = res.scalar_one_or_none()
    if not mem:
        mem = PersonalSegmentMemory(
            user_id=user_id,
            osm_segment_id=osm_segment_id,
            visit_count=1,
            selection_count=1,
            rejection_count=0,
            negative_feedback_count=2,
            avoidance_score=0.70,
            last_visit=datetime.utcnow(),
        )
        db.add(mem)
    else:
        mem.negative_feedback_count += 2
        mem.avoidance_score = min(1.0, mem.avoidance_score + 0.35)

    _recalculate_memory_metrics(mem)
    await db.commit()


async def get_user_segment_memories_map(
    user_id: Optional[int],
    db: AsyncSession,
) -> Dict[str, Dict[str, Any]]:
    """
    Fetches all active segment memory entries for a user as an in-memory dictionary.
    """
    if not user_id:
        return {}

    res = await db.execute(
        select(PersonalSegmentMemory).where(PersonalSegmentMemory.user_id == user_id)
    )
    rows = res.scalars().all()
    memory_map = {}
    for r in rows:
        memory_map[r.osm_segment_id] = {
            "visit_count": r.visit_count,
            "selection_count": r.selection_count,
            "rejection_count": r.rejection_count,
            "trust_score": r.trust_score,
            "avoidance_score": r.avoidance_score,
            "confidence": r.confidence,
            "personal_risk_adjustment": r.personal_risk_adjustment,
        }
    return memory_map


def evaluate_route_segment_memory(
    route_segment_ids: List[str],
    segment_memories: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Evaluates a candidate route against a user's personal segment memory.
    Returns:
    - segment_memory_adjustment: net delta risk to add to personalized risk
    - familiar_segments_count: count of segments user is familiar with (visit_count >= 2)
    - avoided_segments_count: count of segments user has avoided (avoidance_score >= 0.35)
    - has_critical_avoidance: true if route traverses a high-avoidance road (avoidance_score >= 0.70)
    """
    if not route_segment_ids or not segment_memories:
        return {
            "segment_memory_adjustment": 0.0,
            "familiar_segments_count": 0,
            "avoided_segments_count": 0,
            "has_critical_avoidance": False,
        }

    deltas = []
    familiar_count = 0
    avoided_count = 0
    has_critical = False

    for seg_id in route_segment_ids:
        mem = segment_memories.get(str(seg_id))
        if mem:
            deltas.append(mem.get("personal_risk_adjustment", 0.0))
            if mem.get("visit_count", 0) >= 2 or mem.get("trust_score", 0.0) >= 0.65:
                familiar_count += 1
            if mem.get("avoidance_score", 0.0) >= 0.35 or mem.get("rejection_count", 0) >= 3:
                avoided_count += 1
            if mem.get("avoidance_score", 0.0) >= 0.70:
                has_critical = True

    if not deltas:
        avg_delta = 0.0
    else:
        # Proportion of route segments having memory influence
        coverage = min(1.0, len(deltas) / max(1, len(route_segment_ids)))
        avg_delta = float(np.mean(deltas)) * coverage

    # Critical avoidance penalty
    if has_critical:
        avg_delta += 15.0

    return {
        "segment_memory_adjustment": round(float(np.clip(avg_delta, -15.0, 25.0)), 2),
        "familiar_segments_count": familiar_count,
        "avoided_segments_count": avoided_count,
        "has_critical_avoidance": has_critical,
    }
