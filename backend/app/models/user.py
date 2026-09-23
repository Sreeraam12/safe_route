from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    preferences = relationship("PersonalPreferences", back_populates="user", uselist=False, lazy="selectin", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")
    twin_state = relationship("PersonalTwinState", back_populates="user", uselist=False, lazy="selectin", cascade="all, delete-orphan")
    segment_memories = relationship("PersonalSegmentMemory", back_populates="user", cascade="all, delete-orphan")


class PersonalPreferences(Base):
    __tablename__ = "personal_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # User's explicit baseline preferences (0.0 to 1.0)
    lighting_preference = Column(Float, default=0.7)
    crowd_preference = Column(Float, default=0.6)
    isolation_aversion = Column(Float, default=0.8)
    cctv_preference = Column(Float, default=0.6)
    police_proximity_preference = Column(Float, default=0.7)
    main_road_preference = Column(Float, default=0.75)
    crime_sensitivity = Column(Float, default=0.85)
    traffic_tolerance = Column(Float, default=0.4)
    distance_priority = Column(Float, default=0.3)
    time_priority = Column(Float, default=0.4)
    detour_tolerance = Column(Float, default=0.25)  # 25% max detour for safety
    night_safety_weight = Column(Float, default=0.85)
    weather_sensitivity = Column(Float, default=0.5)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="preferences")
