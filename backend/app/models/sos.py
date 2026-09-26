import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from backend.app.db.session import Base
from backend.app.models.trusted_contact import TrustedContact


class SOSEvent(Base):
    __tablename__ = "sos_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_id = Column(String, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(30), default="ACTIVE", nullable=False, index=True)
    trigger_lat = Column(Float, nullable=False)
    trigger_lon = Column(Float, nullable=False)
    latest_lat = Column(Float, nullable=False)
    latest_lon = Column(Float, nullable=False)
    segment_id = Column(String(120), nullable=True)
    road_name = Column(String(200), nullable=True)
    nearest_police_station_name = Column(String(200), nullable=True)
    nearest_police_station_lat = Column(Float, nullable=True)
    nearest_police_station_lon = Column(Float, nullable=True)
    nearest_police_station_distance_km = Column(Float, nullable=True)
    share_token = Column(String(120), unique=True, index=True, nullable=True)
    resolution_type = Column(String(50), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SOSLocationUpdate(Base):
    __tablename__ = "sos_location_updates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sos_id = Column(String, ForeignKey("sos_events.id", ondelete="CASCADE"), nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    speed = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class SOSNotification(Base):
    __tablename__ = "sos_notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sos_id = Column(String, ForeignKey("sos_events.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_contact_id = Column(String, ForeignKey("trusted_contacts.id", ondelete="SET NULL"), nullable=True)
    channel = Column(String(30), nullable=False)
    delivery_status = Column(String(30), default="SENT", nullable=False)
    message_summary = Column(String(500), nullable=True)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class SafetyEvent(Base):
    __tablename__ = "safety_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sos_id = Column(String, ForeignKey("sos_events.id", ondelete="SET NULL"), nullable=True, index=True)
    segment_id = Column(String(120), nullable=True, index=True)
    road_name = Column(String(200), nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    event_type = Column(String(50), default="SOS_TRIGGERED", nullable=False)
    verification_status = Column(String(30), default="UNVERIFIED", nullable=False)
    confidence = Column(Float, default=0.30, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
