import json
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.trip import Trip, RouteInteraction, TripFeedback
from backend.app.schemas.trip import (
    TripCreateRequest,
    TripResponse,
    TripFeedbackRequest,
    TripFeedbackResponse,
)
from backend.app.api.deps import get_optional_user, get_current_user
from backend.app.services.personal_twin_engine import learn_from_trip_feedback
from backend.app.services.segment_memory_service import (
    record_route_selection_and_rejections,
    record_trip_traversal,
    record_trip_feedback_on_segments,
)

router = APIRouter(prefix="/api/trips", tags=["Trips & Feedback"])


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    request: TripCreateRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    trip_id = f"trip_{uuid.uuid4().hex[:16]}"
    user_id = current_user.id if current_user else None

    trip = Trip(
        id=trip_id,
        user_id=user_id,
        trip_datetime=datetime.utcnow(),
        travel_date=request.travel_date,
        travel_time=request.travel_time,
        source_zone=request.source_zone,
        destination_zone=request.destination_zone,
        source_lat=request.source_lat,
        source_lon=request.source_lon,
        dest_lat=request.dest_lat,
        dest_lon=request.dest_lon,
        travel_mode=request.travel_mode,
        trip_intent=request.trip_intent,
        selected_route_id=request.selected_route_id,
        selected_distance_km=request.selected_distance_km,
        selected_duration_min=request.selected_duration_min,
        selected_safety_score=request.selected_safety_score,
        weather_condition=request.weather_condition,
        traffic_condition=request.traffic_condition,
        completed=False,
        traversed_segment_ids=json.dumps(request.selected_segment_ids) if request.selected_segment_ids else None,
    )
    db.add(trip)

    # Add candidate route interactions
    for item in request.interactions:
        interaction = RouteInteraction(
            trip_id=trip_id,
            user_id=user_id,
            route_id=item.route_id,
            route_rank=item.route_rank,
            route_distance_km=item.route_distance_km,
            route_duration_min=item.route_duration_min,
            route_risk=item.route_risk,
            route_safety_score=item.route_safety_score,
            lighting_score=item.lighting_score,
            crowd_score=item.crowd_score,
            isolation_score=item.isolation_score,
            crime_risk=item.crime_risk,
            traffic_risk=item.traffic_risk,
            viewed=item.viewed,
            selected=item.selected,
            rejected=item.rejected,
            rejection_reason=item.rejection_reason,
            osm_segment_ids=json.dumps(item.osm_segment_ids) if item.osm_segment_ids else None,
        )
        db.add(interaction)

    await db.commit()
    await db.refresh(trip)

    # Trigger Personal Segment Memory update for selection and implicit rejections
    if user_id and request.selected_segment_ids:
        candidate_seg_lists = [item.osm_segment_ids for item in request.interactions if item.osm_segment_ids]
        await record_route_selection_and_rejections(
            user_id=user_id,
            selected_segments=request.selected_segment_ids,
            candidate_routes_segments=candidate_seg_lists,
            db=db,
        )

    return trip


@router.get("/history", response_model=List[TripResponse])
async def get_trip_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Trip)
        .where(Trip.user_id == current_user.id)
        .options(selectinload(Trip.feedback))
        .order_by(Trip.trip_datetime.desc())
        .limit(50)
    )
    trips = result.scalars().all()
    return trips


@router.post("/{trip_id}/complete", response_model=TripResponse)
async def complete_trip(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip.completed = True
    await db.commit()
    await db.refresh(trip)

    # Record physical traversal in Personal Segment Memory
    if trip.user_id and trip.traversed_segment_ids:
        try:
            segments = json.loads(trip.traversed_segment_ids)
            if isinstance(segments, list) and segments:
                await record_trip_traversal(trip.user_id, segments, db)
        except Exception:
            pass

    return trip


@router.post("/{trip_id}/feedback", response_model=TripFeedbackResponse)
async def submit_trip_feedback(
    trip_id: str,
    request: TripFeedbackRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Check existing feedback
    existing = await db.execute(select(TripFeedback).where(TripFeedback.trip_id == trip_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Feedback already submitted for this trip")

    user_id = current_user.id if current_user else trip.user_id

    feedback = TripFeedback(
        trip_id=trip_id,
        user_id=user_id,
        safety_rating=request.safety_rating,
        comfort_rating=request.comfort_rating,
        lighting_rating=request.lighting_rating,
        crowd_rating=request.crowd_rating,
        navigation_rating=request.navigation_rating,
        incident_reported=request.incident_reported,
        incident_type=request.incident_type,
        felt_unsafe=request.felt_unsafe,
        feedback_text=request.feedback_text,
    )
    db.add(feedback)
    trip.completed = True

    await db.commit()
    await db.refresh(feedback)

    # Trigger Personal Twin learning if associated with a user
    if user_id:
        await learn_from_trip_feedback(user_id, trip, feedback, db)

        # Trigger Personal Segment Memory feedback update on traversed corridors
        if trip.traversed_segment_ids:
            try:
                segments = json.loads(trip.traversed_segment_ids)
                if isinstance(segments, list) and segments:
                    await record_trip_feedback_on_segments(
                        user_id=user_id,
                        traversed_segments=segments,
                        felt_unsafe=feedback.felt_unsafe,
                        safety_rating=feedback.safety_rating,
                        incident_reported=feedback.incident_reported,
                        db=db,
                    )
            except Exception:
                pass

    return feedback

