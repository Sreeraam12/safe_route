from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TrustedContactCreate(BaseModel):
    name: Optional[str] = "Trusted Contact"
    contact_name: Optional[str] = None
    phone_number: str = Field(..., min_length=3, max_length=30)
    relationship: Optional[str] = Field("Family", max_length=80)
    is_primary: Optional[bool] = False


class TrustedContactUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    phone_number: Optional[str] = None
    relationship: Optional[str] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class TrustedContactResponse(BaseModel):
    id: str
    contact_id: Optional[str] = None
    owner_user_id: int
    contact_user_id: Optional[int] = None
    name: str
    contact_name: Optional[str] = None
    phone_number: str
    relationship: Optional[str] = None
    is_verified: bool = True
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SOSActivateRequest(BaseModel):
    trip_id: Optional[str] = None
    route_id: Optional[str] = None
    latitude: float
    longitude: float
    speed: Optional[float] = None
    trigger_type: Optional[str] = "manual"
    user_notes: Optional[str] = None


class SOSLocationUpdateRequest(BaseModel):
    sos_id: Optional[str] = None
    latitude: float
    longitude: float
    speed: Optional[float] = None


class SOSResolveRequest(BaseModel):
    resolution_notes: Optional[str] = None
    resolution_type: Optional[str] = None
