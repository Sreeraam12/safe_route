from datetime import date, time
from typing import Optional
from pydantic import BaseModel, field_validator

class GeocodeRequest(BaseModel):
    place: str


class GeocodeResponse(BaseModel):
    name: str
    latitude: float
    longitude: float

class RouteSearchRequest(BaseModel):
    source: str
    destination: str
    travel_date: Optional[date] = None
    travel_time: Optional[time] = None
    travel_mode: str = "driving"

    @field_validator("travel_time")
    @classmethod
    def validate_travel_time(cls, value: Optional[time]) -> Optional[time]:
        if value is not None and (value.second != 0 or value.microsecond != 0):
            raise ValueError(
                "Travel time must be in HH:MM format."
            )

        return value