import secrets
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.sos import SOSEvent, SOSLocationUpdate, SafetyEvent
from backend.app.models.trusted_contact import TrustedContact
from backend.app.services.police_station_service import find_nearest_police_station
from backend.app.services.notification_service import send_sos_notification
from backend.app.services.route_engine import GRAPH, find_nearest_node


def identify_current_road_segment(lat: float, lon: float) -> Tuple[str, str]:
    """
    Snap user's GPS coordinate to the nearest OSM road segment in GRAPH.
    Returns (segment_id, road_name).
    """
    try:
        u = find_nearest_node(GRAPH, lat, lon)
        edges = list(GRAPH.edges(u, keys=True, data=True))
        if edges:
            u_node, v_node, key, data = edges[0]
            seg_id = f"{u_node}_{v_node}_{key}"
            name = data.get("name")
            if isinstance(name, list):
                name = name[0]
            road_name = str(name) if name else "Chennai Road Segment"
            return seg_id, road_name
    except Exception:
        pass
    return f"seg_{round(lat, 3)}_{round(lon, 3)}", "Chennai Road Network"


async def activate_sos(
    db: AsyncSession,
    user_id: str,
    traveler_name: str,
    trip_id: Optional[str],
    latitude: float,
    longitude: float,
    speed: Optional[float] = None,
) -> SOSEvent:
    # Check if an ACTIVE SOS already exists for this user (prevent duplicate active SOS)
    existing_stmt = select(SOSEvent).where(
        SOSEvent.user_id == user_id,
        SOSEvent.status == "ACTIVE",
    )
    res = await db.execute(existing_stmt)
    existing_sos = res.scalar_one_or_none()
    if existing_sos:
        return existing_sos

    seg_id, road_name = identify_current_road_segment(latitude, longitude)
    police_info = find_nearest_police_station(latitude, longitude)
    share_token = secrets.token_urlsafe(24)

    sos = SOSEvent(
        user_id=user_id,
        trip_id=trip_id,
        status="ACTIVE",
        trigger_lat=latitude,
        trigger_lon=longitude,
        latest_lat=latitude,
        latest_lon=longitude,
        segment_id=seg_id,
        road_name=road_name,
        nearest_police_station_name=police_info["name"],
        nearest_police_station_lat=police_info["lat"],
        nearest_police_station_lon=police_info["lon"],
        nearest_police_station_distance_km=police_info["distance_km"],
        share_token=share_token,
    )
    db.add(sos)
    await db.flush()

    # Record initial location point
    loc_point = SOSLocationUpdate(
        sos_id=sos.id,
        lat=latitude,
        lon=longitude,
        speed=speed,
    )
    db.add(loc_point)

    # Record Phase-2 unverified contextual safety signal (confidence=0.30, 24h expiry)
    safety_evt = SafetyEvent(
        sos_id=sos.id,
        segment_id=seg_id,
        road_name=road_name,
        lat=latitude,
        lon=longitude,
        event_type="SOS_TRIGGERED",
        verification_status="UNVERIFIED",
        confidence=0.30,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(safety_evt)

    # Notify active trusted contacts (never fail SOS creation if notification fails)
    try:
        contacts_res = await db.execute(
            select(TrustedContact).where(
                TrustedContact.owner_user_id == user_id,
                TrustedContact.is_active == True,  # noqa: E712
            )
        )
        contacts = list(contacts_res.scalars().all())
        await send_sos_notification(db, sos, traveler_name, contacts)
    except Exception as e:
        print(f"[SOS Warning] Notification dispatch error: {e}")

    await db.commit()
    await db.refresh(sos)
    return sos


async def record_sos_location_update(
    db: AsyncSession,
    sos: SOSEvent,
    latitude: float,
    longitude: float,
    speed: Optional[float] = None,
) -> SOSEvent:
    seg_id, road_name = identify_current_road_segment(latitude, longitude)
    police_info = find_nearest_police_station(latitude, longitude)

    sos.latest_lat = latitude
    sos.latest_lon = longitude
    sos.segment_id = seg_id
    sos.road_name = road_name
    sos.nearest_police_station_name = police_info["name"]
    sos.nearest_police_station_lat = police_info["lat"]
    sos.nearest_police_station_lon = police_info["lon"]
    sos.nearest_police_station_distance_km = police_info["distance_km"]
    sos.updated_at = datetime.now(timezone.utc)

    loc_point = SOSLocationUpdate(
        sos_id=sos.id,
        lat=latitude,
        lon=longitude,
        speed=speed,
    )
    db.add(loc_point)
    await db.commit()
    await db.refresh(sos)
    return sos


async def cancel_or_resolve_sos(
    db: AsyncSession,
    sos: SOSEvent,
    new_status: str,
    resolution_type: str,
) -> SOSEvent:
    sos.status = new_status
    sos.resolution_type = resolution_type
    sos.resolved_at = datetime.now(timezone.utc)
    sos.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(sos)
    return sos
