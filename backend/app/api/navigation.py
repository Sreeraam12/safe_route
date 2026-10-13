from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.navigation import (
    NavigationStartRequest,
    GPSUpdateRequest,
    NavigationStatusResponse,
    ManualRerouteRequest,
)
from backend.app.services.navigation_engine import (
    start_navigation_session,
    get_navigation_session,
    end_navigation_session,
    update_navigation_progress,
)
from backend.app.services.rerouting_engine import recalculate_safe_route
from backend.app.services.personal_twin_engine import get_effective_twin_weights
from backend.app.api.deps import get_optional_user

router = APIRouter(prefix="/api/navigation", tags=["Live Navigation"])


@router.post("/start")
async def start_navigation(request: NavigationStartRequest):
    session = start_navigation_session(
        trip_id=request.trip_id,
        geometry=request.geometry,
        instructions=request.instructions,
        destination_lat=request.destination_lat,
        destination_lon=request.dest_lon,
    )
    return {"status": "started", "trip_id": request.trip_id}


@router.post("/update", response_model=NavigationStatusResponse)
async def update_gps(
    request: GPSUpdateRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    session = get_navigation_session(request.trip_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Navigation session for trip {request.trip_id} not found. Please start navigation first.",
        )

    # 1. Update progress
    progress = update_navigation_progress(
        trip_id=request.trip_id,
        gps_lat=request.latitude,
        gps_lon=request.longitude,
        speed_kmh=request.speed,
    )

    new_route = None

    # 2. Trigger dynamic re-routing if off-route confirmed
    if progress["rerouting"]:
        twin_weights = await get_effective_twin_weights(
            current_user.id if current_user else None,
            db,
        )
        try:
            new_route = await recalculate_safe_route(
                trip_id=request.trip_id,
                current_lat=request.latitude,
                current_lon=request.longitude,
                destination_lat=session["destination_lat"],
                dest_lon=session["destination_lon"],
                twin_weights=twin_weights,
            )
            # Recompute progress immediately on new route
            progress = update_navigation_progress(
                trip_id=request.trip_id,
                gps_lat=request.latitude,
                gps_lon=request.longitude,
                speed_kmh=request.speed,
            )
        except Exception as e:
            print(f"[SafeRoute Re-route Error] {e}")

    progress["new_route"] = new_route
    return progress


@router.post("/reroute")
async def manual_reroute(
    request: ManualRerouteRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    twin_weights = await get_effective_twin_weights(
        current_user.id if current_user else None,
        db,
    )
    new_route = await recalculate_safe_route(
        trip_id=request.trip_id,
        current_lat=request.current_lat,
        current_lon=request.current_lon,
        destination_lat=request.destination_lat,
        dest_lon=request.dest_lon,
        twin_weights=twin_weights,
    )
    return {"status": "rerouted", "new_route": new_route}


@router.post("/end")
async def end_navigation(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
):
    session = end_navigation_session(trip_id)

    # Mark trip complete and record physical traversal in Personal Segment Memory
    try:
        from sqlalchemy import select
        from backend.app.models.trip import Trip
        import json
        from backend.app.services.segment_memory_service import record_trip_traversal

        res = await db.execute(select(Trip).where(Trip.id == trip_id))
        trip = res.scalar_one_or_none()
        if trip:
            trip.completed = True
            if trip.user_id and trip.traversed_segment_ids:
                segments = json.loads(trip.traversed_segment_ids)
                if isinstance(segments, list) and segments:
                    await record_trip_traversal(trip.user_id, segments, db)
            await db.commit()
    except Exception as e:
        print(f"[SafeRoute Navigation End Error] {e}")

    return {"status": "ended", "trip_id": trip_id}

