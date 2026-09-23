from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2)


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PreferencesUpdateRequest(BaseModel):
    lighting_preference: Optional[float] = Field(None, ge=0.0, le=1.0)
    crowd_preference: Optional[float] = Field(None, ge=0.0, le=1.0)
    isolation_aversion: Optional[float] = Field(None, ge=0.0, le=1.0)
    cctv_preference: Optional[float] = Field(None, ge=0.0, le=1.0)
    police_proximity_preference: Optional[float] = Field(None, ge=0.0, le=1.0)
    main_road_preference: Optional[float] = Field(None, ge=0.0, le=1.0)
    crime_sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)
    traffic_tolerance: Optional[float] = Field(None, ge=0.0, le=1.0)
    distance_priority: Optional[float] = Field(None, ge=0.0, le=1.0)
    time_priority: Optional[float] = Field(None, ge=0.0, le=1.0)
    detour_tolerance: Optional[float] = Field(None, ge=0.0, le=1.0)
    night_safety_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    weather_sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)


class PreferencesResponse(BaseModel):
    user_id: int
    lighting_preference: float
    crowd_preference: float
    isolation_aversion: float
    cctv_preference: float
    police_proximity_preference: float
    main_road_preference: float
    crime_sensitivity: float
    traffic_tolerance: float
    distance_priority: float
    time_priority: float
    detour_tolerance: float
    night_safety_weight: float
    weather_sensitivity: float
    updated_at: datetime

    class Config:
        from_attributes = True


class TwinStateResponse(BaseModel):
    user_id: int
    timestamp: datetime
    lighting_weight: float
    crime_weight: float
    isolation_weight: float
    crowd_weight: float
    traffic_weight: float
    distance_weight: float
    time_weight: float
    night_weight: float
    weather_weight: float
    detour_tolerance: float
    model_confidence: float

    class Config:
        from_attributes = True
