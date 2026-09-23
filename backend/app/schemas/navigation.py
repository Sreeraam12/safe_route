from typing import Optional, List, Tuple
from pydantic import BaseModel, Field


class NavigationStartRequest(BaseModel):
    trip_id: str
    selected_route_index: int
    geometry: List[List[float]]  # list of [lon, lat] coordinates
    instructions: List[dict]
    destination_lat: float
    dest_lon: float


class GPSUpdateRequest(BaseModel):
    trip_id: str
    latitude: float
    longitude: float
    speed: Optional[float] = None       # km/h
    heading: Optional[float] = None     # degrees [0, 360]
    accuracy: Optional[float] = None   # meters


class NavigationStatusResponse(BaseModel):
    trip_id: str
    current_instruction: str
    next_instruction: Optional[str] = None
    step_number: int
    total_steps: int
    distance_to_turn_m: float
    distance_to_turn_formatted: str
    remaining_distance_km: float
    eta_minutes: float
    off_route: bool
    consecutive_deviations: int
    rerouting: bool
    is_at_destination: bool
    new_route: Optional[dict] = None  # populated if dynamic re-route occurred


class ManualRerouteRequest(BaseModel):
    trip_id: str
    current_lat: float
    current_lon: float
    destination_lat: float
    dest_lon: float
    reason: Optional[str] = "user_requested"

