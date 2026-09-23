from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Time, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class Trip(Base):
    __tablename__ = "trips"

    id = Column(String(64), primary_key=True, index=True)  # UUID or trip token
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    trip_datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    travel_date = Column(Date, nullable=False)
    travel_time = Column(Time, nullable=False)

    source_zone = Column(String(255), nullable=False)
    destination_zone = Column(String(255), nullable=False)
    source_lat = Column(Float, nullable=False)
    source_lon = Column(Float, nullable=False)
    dest_lat = Column(Float, nullable=False)
    dest_lon = Column(Float, nullable=False)

    travel_mode = Column(String(50), default="driving", nullable=False)
    trip_intent = Column(String(100), nullable=True)

    selected_route_id = Column(Integer, nullable=True)
    selected_distance_km = Column(Float, nullable=True)
    selected_duration_min = Column(Float, nullable=True)
    selected_safety_score = Column(Float, nullable=True)

    actual_distance_km = Column(Float, nullable=True)
    actual_duration_min = Column(Float, nullable=True)
    route_deviation_pct = Column(Float, default=0.0)

    weather_condition = Column(String(100), nullable=True)
    traffic_condition = Column(String(100), nullable=True)

    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="trips")
    interactions = relationship("RouteInteraction", back_populates="trip", lazy="selectin", cascade="all, delete-orphan")
    feedback = relationship("TripFeedback", back_populates="trip", uselist=False, lazy="selectin", cascade="all, delete-orphan")


class RouteInteraction(Base):
    __tablename__ = "route_interactions"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(String(64), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    route_id = Column(Integer, nullable=False)
    route_rank = Column(Integer, nullable=False)
    route_distance_km = Column(Float, nullable=False)
    route_duration_min = Column(Float, nullable=True)
    route_risk = Column(Float, nullable=False)
    route_safety_score = Column(Float, nullable=False)

    lighting_score = Column(Float, nullable=True)
    crowd_score = Column(Float, nullable=True)
    isolation_score = Column(Float, nullable=True)
    crime_risk = Column(Float, nullable=True)
    traffic_risk = Column(Float, nullable=True)

    viewed = Column(Boolean, default=True)
    selected = Column(Boolean, default=False)
    rejected = Column(Boolean, default=False)
    rejection_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    trip = relationship("Trip", back_populates="interactions")


class TripFeedback(Base):
    __tablename__ = "trip_feedback"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(String(64), ForeignKey("trips.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    safety_rating = Column(Integer, nullable=False)  # 1 to 5
    comfort_rating = Column(Integer, nullable=True)
    lighting_rating = Column(Integer, nullable=True)
    crowd_rating = Column(Integer, nullable=True)
    navigation_rating = Column(Integer, nullable=True)

    incident_reported = Column(Boolean, default=False)
    incident_type = Column(String(100), nullable=True)
    felt_unsafe = Column(Boolean, default=False)
    feedback_text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    trip = relationship("Trip", back_populates="feedback")
