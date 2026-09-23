from datetime import datetime, date, time
from typing import Optional, List
from pydantic import BaseModel, Field


class RouteInteractionCreate(BaseModel):
    route_id: int
    route_rank: int
    route_distance_km: float
    route_duration_min: Optional[float] = None
    route_risk: float
    route_safety_score: float
    lighting_score: Optional[float] = None
    crowd_score: Optional[float] = None
    isolation_score: Optional[float] = None
    crime_risk: Optional[float] = None
    traffic_risk: Optional[float] = None
    viewed: bool = True
    selected: bool = False
    rejected: bool = False
    rejection_reason: Optional[str] = None


class TripCreateRequest(BaseModel):
    travel_date: date
    travel_time: time
    source_zone: str
    destination_zone: str
    source_lat: float
    source_lon: float
    dest_lat: float
    dest_lon: float
    travel_mode: str = "driving"
    trip_intent: Optional[str] = None
    selected_route_id: int
    selected_distance_km: float
    selected_duration_min: Optional[float] = None
    selected_safety_score: float
    weather_condition: Optional[str] = None
    traffic_condition: Optional[str] = None
    interactions: List[RouteInteractionCreate] = []


class TripFeedbackRequest(BaseModel):
    safety_rating: int = Field(..., ge=1, le=5)
    comfort_rating: Optional[int] = Field(None, ge=1, le=5)
    lighting_rating: Optional[int] = Field(None, ge=1, le=5)
    crowd_rating: Optional[int] = Field(None, ge=1, le=5)
    navigation_rating: Optional[int] = Field(None, ge=1, le=5)
    incident_reported: bool = False
    incident_type: Optional[str] = None
    felt_unsafe: bool = False
    feedback_text: Optional[str] = None


class TripFeedbackResponse(BaseModel):
    id: int
    trip_id: str
    safety_rating: int
    incident_reported: bool
    felt_unsafe: bool
    feedback_text: Optional[str]
    comfort_rating: Optional[int] = None
    lighting_rating: Optional[int] = None
    crowd_rating: Optional[int] = None
    navigation_rating: Optional[int] = None
    incident_reported: bool = False
    incident_type: Optional[str] = None
    felt_unsafe: bool = False
    feedback_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TripResponse(BaseModel):
    id: str
    user_id: Optional[int]
    trip_datetime: datetime
    travel_date: date
    travel_time: time
    source_zone: str
    destination_zone: str
    source_lat: float
    source_lon: float
    dest_lat: float
    dest_lon: float
    travel_mode: str
    selected_route_id: Optional[int]
    selected_distance_km: Optional[float]
    selected_safety_score: Optional[float]
    completed: bool
    created_at: datetime
    feedback: Optional[TripFeedbackResponse] = None

    class Config:
        from_attributes = True

