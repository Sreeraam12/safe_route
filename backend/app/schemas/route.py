from pydantic import BaseModel


class GeocodeRequest(BaseModel):
    place: str


class GeocodeResponse(BaseModel):
    name: str
    latitude: float
    longitude: float


class RouteSearchRequest(BaseModel):
    source: str
    destination: str