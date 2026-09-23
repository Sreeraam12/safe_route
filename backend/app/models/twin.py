from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class PersonalSegmentMemory(Base):
    __tablename__ = "personal_segment_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    osm_segment_id = Column(String(100), nullable=False, index=True)

    visit_count = Column(Integer, default=0, nullable=False)
    selection_count = Column(Integer, default=0, nullable=False)
    rejection_count = Column(Integer, default=0, nullable=False)
    positive_feedback_count = Column(Integer, default=0, nullable=False)
    negative_feedback_count = Column(Integer, default=0, nullable=False)

    avoidance_score = Column(Float, default=0.0, nullable=False)  # 0.0 to 1.0 (high = user actively avoids)
    trust_score = Column(Float, default=0.5, nullable=False)      # 0.0 to 1.0 (high = user feels comfortable)
    personal_risk_adjustment = Column(Float, default=0.0, nullable=False)  # delta risk in [-20.0, +20.0]
    
    last_visit = Column(DateTime, nullable=True)
    confidence = Column(Float, default=0.0, nullable=False)       # confidence in this memory (0.0 to 1.0)

    user = relationship("User", back_populates="segment_memories")

    __table_args__ = (
        Index("idx_user_segment", "user_id", "osm_segment_id", unique=True),
    )


class PersonalTwinState(Base):
    __tablename__ = "personal_twin_state"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Current learned weights (normalized in [0.0, 1.0])
    lighting_weight = Column(Float, default=0.20, nullable=False)
    crime_weight = Column(Float, default=0.25, nullable=False)
    isolation_weight = Column(Float, default=0.20, nullable=False)
    crowd_weight = Column(Float, default=0.15, nullable=False)
    traffic_weight = Column(Float, default=0.10, nullable=False)
    distance_weight = Column(Float, default=0.10, nullable=False)
    time_weight = Column(Float, default=0.15, nullable=False)
    night_weight = Column(Float, default=0.20, nullable=False)
    weather_weight = Column(Float, default=0.05, nullable=False)

    detour_tolerance = Column(Float, default=0.25, nullable=False)
    model_confidence = Column(Float, default=0.10, nullable=False)  # increases with completed trips and feedback

    user = relationship("User", back_populates="twin_state")

