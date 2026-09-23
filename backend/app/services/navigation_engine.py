"""
SafeRoute Live Navigation Engine
================================
Maintains live trip navigation sessions, tracks turn-by-turn guidance progress,
detects off-route conditions, and triggers dynamic re-routing.

Conforms to SafeRoute Final Architecture Roadmap (Sections 53A-53L).
"""

from typing import Dict, Any, Optional, List
from backend.app.services.gps_map_matcher import match_gps_to_route, haversine_distance_m

OFF_ROUTE_THRESHOLD_METERS = 50.0  # Deviation distance to consider off-route
REQUIRED_OFF_ROUTE_PINGS = 2       # Consecutive pings before triggering re-route
DESTINATION_ARRIVAL_METERS = 35.0  # Within 35m counts as arrival

# In-memory session store for active trips
_ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}


def start_navigation_session(
    trip_id: str,
    geometry: List[List[float]],
    instructions: List[dict],
    destination_lat: float,
    destination_lon: float,
) -> Dict[str, Any]:
    """Initialize an active live navigation session."""
    session = {
        "trip_id": trip_id,
        "geometry": geometry,
        "instructions": instructions,
        "destination_lat": destination_lat,
        "destination_lon": destination_lon,
        "consecutive_deviations": 0,
        "current_step_index": 0,
        "is_at_destination": False,
        "status": "navigating",
    }
    _ACTIVE_SESSIONS[trip_id] = session
    return session


def get_navigation_session(trip_id: str) -> Optional[Dict[str, Any]]:
    return _ACTIVE_SESSIONS.get(trip_id)


def end_navigation_session(trip_id: str) -> Optional[Dict[str, Any]]:
    return _ACTIVE_SESSIONS.pop(trip_id, None)


def format_distance(distance_m: float) -> str:
    if distance_m < 1000.0:
        return f"{int(round(distance_m))} m"
    return f"{distance_m / 1000.0:.1f} km"


def update_navigation_progress(
    trip_id: str,
    gps_lat: float,
    gps_lon: float,
    speed_kmh: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Process an incoming GPS ping and compute navigation progress.
    """
    session = _ACTIVE_SESSIONS.get(trip_id)
    if not session:
        raise ValueError(f"No active navigation session for trip {trip_id}")

    geometry = session["geometry"]
    instructions = session["instructions"]
    dest_lat = session["destination_lat"]
    dest_lon = session["destination_lon"]

    # 1. Check if user has arrived at destination
    dist_to_destination = haversine_distance_m(gps_lat, gps_lon, dest_lat, dest_lon)
    if dist_to_destination <= DESTINATION_ARRIVAL_METERS:
        session["is_at_destination"] = True
        session["status"] = "arrived"
        return {
            "trip_id": trip_id,
            "current_instruction": "You have arrived at your destination",
            "next_instruction": None,
            "step_number": len(instructions),
            "total_steps": len(instructions),
            "distance_to_turn_m": 0.0,
            "distance_to_turn_formatted": "0 m",
            "remaining_distance_km": 0.0,
            "eta_minutes": 0.0,
            "off_route": False,
            "consecutive_deviations": 0,
            "rerouting": False,
            "is_at_destination": True,
        }

    # 2. Map-match to route
    match_result = match_gps_to_route(gps_lat, gps_lon, geometry)
    min_dist_m = match_result["min_distance_m"]
    remaining_dist_m = match_result["remaining_distance_m"]

    # 3. Off-route detection with confirmation window
    off_route = min_dist_m > OFF_ROUTE_THRESHOLD_METERS
    if off_route:
        session["consecutive_deviations"] += 1
    else:
        session["consecutive_deviations"] = 0

    should_reroute = session["consecutive_deviations"] >= REQUIRED_OFF_ROUTE_PINGS

    # 4. Determine current instruction step based on progress
    # Fraction of route completed
    total_dist_m = match_result["total_route_distance_m"]
    dist_along_m = match_result["distance_along_route_m"]
    num_instructions = len(instructions)

    step_idx = 0
    accumulated_instruction_dist = 0.0
    for idx, inst in enumerate(instructions):
        step_len = float(inst.get("distance_m", 0.0))
        accumulated_instruction_dist += step_len
        if dist_along_m <= accumulated_instruction_dist or idx == num_instructions - 1:
            step_idx = idx
            break

    session["current_step_index"] = step_idx
    curr_inst = instructions[step_idx]
    next_inst = instructions[step_idx + 1] if step_idx + 1 < num_instructions else None

    # Distance to next turn
    dist_to_turn = max(0.0, accumulated_instruction_dist - dist_along_m)

    # ETA: assume current speed or 25 km/h urban default
    effective_speed_kmh = max(speed_kmh if speed_kmh and speed_kmh > 5.0 else 25.0, 5.0)
    eta_min = (remaining_dist_m / 1000.0) / effective_speed_kmh * 60.0

    return {
        "trip_id": trip_id,
        "current_instruction": curr_inst.get("instruction", "Continue on route"),
        "next_instruction": next_inst.get("instruction") if next_inst else None,
        "step_number": step_idx + 1,
        "total_steps": num_instructions,
        "distance_to_turn_m": round(dist_to_turn, 1),
        "distance_to_turn_formatted": format_distance(dist_to_turn),
        "remaining_distance_km": round(remaining_dist_m / 1000.0, 2),
        "eta_minutes": round(eta_min, 1),
        "off_route": off_route,
        "consecutive_deviations": session["consecutive_deviations"],
        "rerouting": should_reroute,
        "is_at_destination": False,
    }


def update_session_with_new_route(
    trip_id: str,
    new_geometry: List[List[float]],
    new_instructions: List[dict],
):
    """Update active navigation session after a successful re-routing event."""
    session = _ACTIVE_SESSIONS.get(trip_id)
    if session:
        session["geometry"] = new_geometry
        session["instructions"] = new_instructions
        session["consecutive_deviations"] = 0
        session["current_step_index"] = 0

