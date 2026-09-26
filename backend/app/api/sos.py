import re
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import Base, get_db, engine
from backend.app.models.user import User
from backend.app.models.trusted_contact import TrustedContact
from backend.app.models.sos import SOSEvent, SOSLocationUpdate, SOSNotification, SafetyEvent
from backend.app.schemas.sos import (
    TrustedContactCreate,
    TrustedContactUpdate,
    TrustedContactResponse,
    SOSActivateRequest,
    SOSLocationUpdateRequest,
)
from backend.app.services.police_station_service import (
    find_nearest_police_station,
    identify_current_road_segment,
)
from backend.app.services.notification_service import (
    dispatch_sos_notifications,
    dispatch_sos_status_update,
)
from backend.app.api.deps import get_current_user


emergency_router = APIRouter(prefix="/api/emergency", tags=["Emergency Contacts"])
sos_router = APIRouter(prefix="/api/sos", tags=["SOS Subsystem"])


def _serialize_contact(c: TrustedContact) -> Dict[str, Any]:
    return {
        "id": c.id,
        "contact_id": c.id,
        "owner_user_id": c.owner_user_id,
        "contact_user_id": c.contact_user_id,
        "name": c.name,
        "contact_name": c.name,
        "phone_number": c.phone_number,
        "relationship": c.relationship or "Family",
        "is_verified": c.is_verified,
        "is_active": c.is_active,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


async def _serialize_sos(db: AsyncSession, sos: SOSEvent) -> Dict[str, Any]:
    notif_res = await db.execute(select(SOSNotification).where(SOSNotification.sos_id == sos.id))
    notifs = [
        {
            "id": n.id,
            "channel": n.channel,
            "delivery_status": n.delivery_status,
            "message_summary": n.message_summary,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
        }
        for n in notif_res.scalars().all()
    ]
    contacts_res = await db.execute(
        select(TrustedContact).where(
            TrustedContact.owner_user_id == sos.user_id,
            TrustedContact.is_active == True,
        )
    )
    notified_contacts = [
        {"contact_name": c.name, "phone_number": c.phone_number, "contact_user_id": c.contact_user_id}
        for c in contacts_res.scalars().all()
    ]
    share_url = f"http://localhost:3000/sos/track/{sos.share_token}"
    return {
        "id": sos.id,
        "sos_id": sos.id,
        "user_id": sos.user_id,
        "trip_id": sos.trip_id,
        "status": sos.status,
        "latitude": sos.latest_lat,
        "longitude": sos.latest_lon,
        "trigger_lat": sos.trigger_lat,
        "trigger_lon": sos.trigger_lon,
        "latest_lat": sos.latest_lat,
        "latest_lon": sos.latest_lon,
        "segment_id": sos.segment_id,
        "road_name": sos.road_name,
        "nearest_police_station_name": sos.nearest_police_station_name,
        "nearest_police_station_lat": sos.nearest_police_station_lat,
        "nearest_police_station_lon": sos.nearest_police_station_lon,
        "nearest_police_station_distance_km": sos.nearest_police_station_distance_km,
        "nearest_police_station": {
            "name": sos.nearest_police_station_name or "Chennai Police Patrol",
            "lat": sos.nearest_police_station_lat,
            "lon": sos.nearest_police_station_lon,
            "distance_km": sos.nearest_police_station_distance_km or 0.8,
            "phone": "112 / 044-23452359",
        },
        "share_token": sos.share_token,
        "share_url": share_url,
        "tracking_url": share_url,
        "notified_contacts": notified_contacts,
        "resolution_type": sos.resolution_type,
        "triggered_at": sos.created_at.isoformat() if sos.created_at else None,
        "resolved_at": sos.resolved_at.isoformat() if sos.resolved_at else None,
        "created_at": sos.created_at.isoformat() if sos.created_at else None,
        "updated_at": sos.updated_at.isoformat() if sos.updated_at else None,
        "notifications": notifs,
    }


@emergency_router.get("/contacts")
async def list_trusted_contacts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(TrustedContact)
        .where(TrustedContact.owner_user_id == current_user.id)
        .order_by(TrustedContact.created_at)
    )
    items = [_serialize_contact(c) for c in res.scalars().all()]
    return {"contacts": items, "items": items}


@emergency_router.post("/contacts", status_code=status.HTTP_201_CREATED)
async def create_trusted_contact(
    payload: TrustedContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c_name = (payload.contact_name or payload.name or "Trusted Contact").strip()
    phone_clean = payload.phone_number.strip()
    if not re.fullmatch(r"^\d{10}$", phone_clean):
        raise HTTPException(status_code=400, detail="Phone number must be exactly 10 digits (0-9 only).")

    # Case A (Section 6): Check if contact matches an existing SafeRoute user
    matched_user_id = None
    try:
        u_res = await db.execute(select(User).where(User.name == c_name))
        matched_u = u_res.scalar_one_or_none()
        if matched_u and matched_u.id != current_user.id:
            matched_user_id = matched_u.id
    except Exception:
        pass

    contact = TrustedContact(
        owner_user_id=current_user.id,
        contact_user_id=matched_user_id,
        name=c_name,
        phone_number=phone_clean,
        relationship=(payload.relationship or "Family").strip(),
        is_verified=True,
        is_active=True,
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return _serialize_contact(contact)


@emergency_router.patch("/contacts/{contact_id}")
async def update_trusted_contact(
    contact_id: str,
    payload: TrustedContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(TrustedContact).where(
            TrustedContact.id == contact_id,
            TrustedContact.owner_user_id == current_user.id,
        )
    )
    contact = res.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if payload.name or payload.contact_name:
        contact.name = (payload.contact_name or payload.name).strip()
    if payload.phone_number is not None:
        p_edit = payload.phone_number.strip()
        if not re.fullmatch(r"^\d{10}$", p_edit):
            raise HTTPException(status_code=400, detail="Phone number must be exactly 10 digits (0-9 only).")
        contact.phone_number = p_edit
    if payload.relationship is not None:
        contact.relationship = payload.relationship.strip()
    if payload.is_verified is not None:
        contact.is_verified = payload.is_verified
    if payload.is_active is not None:
        contact.is_active = payload.is_active

    await db.commit()
    await db.refresh(contact)
    return _serialize_contact(contact)


@emergency_router.delete("/contacts/{contact_id}")
async def delete_trusted_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(TrustedContact).where(
            TrustedContact.id == contact_id,
            TrustedContact.owner_user_id == current_user.id,
        )
    )
    contact = res.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    await db.delete(contact)
    await db.commit()
    return {"status": "deleted", "id": contact_id}


@sos_router.post("/activate")
async def trigger_sos_endpoint(
    payload: SOSActivateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Duplicate active SOS prevention (Section 45)
    existing_res = await db.execute(
        select(SOSEvent).where(
            SOSEvent.user_id == current_user.id,
            SOSEvent.status == "ACTIVE",
        )
    )
    existing_sos = existing_res.scalar_one_or_none()
    if existing_sos:
        return await _serialize_sos(db, existing_sos)

    seg_id, road_name = identify_current_road_segment(payload.latitude, payload.longitude)
    police_info = find_nearest_police_station(payload.latitude, payload.longitude)
    share_token = secrets.token_urlsafe(24)

    sos = SOSEvent(
        user_id=current_user.id,
        trip_id=payload.trip_id,
        status="ACTIVE",
        trigger_lat=payload.latitude,
        trigger_lon=payload.longitude,
        latest_lat=payload.latitude,
        latest_lon=payload.longitude,
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

    db.add(
        SOSLocationUpdate(
            sos_id=sos.id,
            lat=payload.latitude,
            lon=payload.longitude,
            speed=payload.speed,
        )
    )
    db.add(
        SafetyEvent(
            sos_id=sos.id,
            segment_id=seg_id,
            road_name=road_name,
            lat=payload.latitude,
            lon=payload.longitude,
            event_type="SOS_TRIGGERED",
            verification_status="UNVERIFIED",
            confidence=0.30,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
    )

    contacts_res = await db.execute(
        select(TrustedContact).where(
            TrustedContact.owner_user_id == current_user.id,
            TrustedContact.is_active == True,
        )
    )
    contacts = list(contacts_res.scalars().all())
    share_url = f"http://localhost:3000/sos/track/{share_token}"
    await dispatch_sos_notifications(db, sos, contacts, share_url)

    await db.commit()
    await db.refresh(sos)
    return await _serialize_sos(db, sos)


@sos_router.get("/active")
async def get_active_sos_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(SOSEvent)
        .where(SOSEvent.user_id == current_user.id, SOSEvent.status == "ACTIVE")
        .order_by(desc(SOSEvent.created_at))
    )
    sos = res.scalar_one_or_none()
    if not sos:
        return None
    return await _serialize_sos(db, sos)


@sos_router.get("/history")
async def get_sos_history_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(SOSEvent)
        .where(SOSEvent.user_id == current_user.id)
        .order_by(desc(SOSEvent.created_at))
        .limit(20)
    )
    events = [await _serialize_sos(db, s) for s in res.scalars().all()]
    return {"sos_events": events, "items": events}


@sos_router.get("/track/{share_token}")
async def track_sos_by_token_endpoint(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(SOSEvent).where(SOSEvent.share_token == share_token))
    sos = res.scalar_one_or_none()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS tracking session not found")
    return await _serialize_sos(db, sos)


@sos_router.get("/{sos_id}")
async def get_sos_detail_endpoint(
    sos_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(SOSEvent).where(
            SOSEvent.id == sos_id,
            SOSEvent.user_id == current_user.id,
        )
    )
    sos = res.scalar_one_or_none()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS event not found")
    return await _serialize_sos(db, sos)


@sos_router.post("/{sos_id}/location")
async def update_sos_location_endpoint(
    sos_id: str,
    payload: SOSLocationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(SOSEvent).where(
            SOSEvent.id == sos_id,
            SOSEvent.user_id == current_user.id,
        )
    )
    sos = res.scalar_one_or_none()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS not found")
    seg_id, road_name = identify_current_road_segment(payload.latitude, payload.longitude)
    police_info = find_nearest_police_station(payload.latitude, payload.longitude)
    sos.latest_lat = payload.latitude
    sos.latest_lon = payload.longitude
    sos.segment_id = seg_id
    sos.road_name = road_name
    sos.nearest_police_station_name = police_info["name"]
    sos.nearest_police_station_lat = police_info["lat"]
    sos.nearest_police_station_lon = police_info["lon"]
    sos.nearest_police_station_distance_km = police_info["distance_km"]
    sos.updated_at = datetime.now(timezone.utc)
    db.add(
        SOSLocationUpdate(
            sos_id=sos.id,
            lat=payload.latitude,
            lon=payload.longitude,
            speed=payload.speed,
        )
    )
    await db.commit()
    await db.refresh(sos)
    return await _serialize_sos(db, sos)


@sos_router.post("/{sos_id}/cancel")
async def cancel_sos_endpoint(
    sos_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(SOSEvent).where(
            SOSEvent.id == sos_id,
            SOSEvent.user_id == current_user.id,
        )
    )
    sos = res.scalar_one_or_none()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS not found")
    sos.status = "CANCELLED"
    sos.resolution_type = "USER_CANCELLED"
    sos.resolved_at = datetime.now(timezone.utc)

    contacts_res = await db.execute(
        select(TrustedContact).where(
            TrustedContact.owner_user_id == current_user.id,
            TrustedContact.is_active == True,
        )
    )
    await dispatch_sos_status_update(db, sos, list(contacts_res.scalars().all()), "CANCELLED")
    await db.commit()
    await db.refresh(sos)
    return await _serialize_sos(db, sos)


@sos_router.post("/{sos_id}/resolve")
async def resolve_sos_endpoint(
    sos_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(SOSEvent).where(
            SOSEvent.id == sos_id,
            SOSEvent.user_id == current_user.id,
        )
    )
    sos = res.scalar_one_or_none()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS not found")
    sos.status = "RESOLVED"
    sos.resolution_type = "USER_SAFE"
    sos.resolved_at = datetime.now(timezone.utc)

    contacts_res = await db.execute(
        select(TrustedContact).where(
            TrustedContact.owner_user_id == current_user.id,
            TrustedContact.is_active == True,
        )
    )
    await dispatch_sos_status_update(db, sos, list(contacts_res.scalars().all()), "RESOLVED (USER SAFE)")
    await db.commit()
    await db.refresh(sos)
    return await _serialize_sos(db, sos)
