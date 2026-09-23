"""
SafeRoute Dynamic Re-Routing Engine
===================================
Calculates a new optimal safe route from the user's CURRENT GPS coordinate to
their destination, applying real-time context (time, traffic, weather, and
Personal Twin preferences).

Conforms to SafeRoute Final Architecture Roadmap (Sections 53F, 53G, 53H, 53I).
"""

from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

from backend.app.services.route_engine import GRAPH, get_nearest_node
from backend.app.services.final_route_engine import calculate_final_route_scores
from backend.app.services.route_geometry import build_route_details
from backend.app.services.navigation_engine import update_session_with_new_route

RISK_DATA = pd.read_pickle("backend/artifacts/osm_hybrid_risk.pkl")


async def recalculate_safe_route(
    trip_id: str,
    current_lat: float,
    current_lon: float,
    destination_lat: float,
    dest_lon: float,
    twin_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Recalculate route starting from user's current GPS position to destination.
    """
    now = datetime.now()

    # Find nearest OSM nodes
    source_node = get_nearest_node(current_lat, current_lon)
    dest_node = get_nearest_node(destination_lat, dest_lon)

    # Generate and score routes from current location
    ranked_routes = await calculate_final_route_scores(
        graph=GRAPH,
        source_node=source_node,
        destination_node=dest_node,
        risk_data=RISK_DATA,
        travel_datetime=now,
        twin_weights=twin_weights,
        num_candidates=10,
        top_k=3,
    )

    if not ranked_routes:
        raise ValueError("Could not find alternative route from current position.")

    top_route = ranked_routes[0]
    route_details = build_route_details(GRAPH, top_route["route"])

    new_route_payload = {
        "route_index": top_route["route_index"],
        "distance_km": route_details["distance_km"],
        "final_risk": top_route["final_risk"],
        "safety_score": top_route["final_safety_score"],
        "personalized_risk": top_route.get("personalized_risk", top_route["final_risk"]),
        "personalized_safety_score": top_route.get("personalized_safety_score", top_route["final_safety_score"]),
        "traffic_risk": top_route["traffic_risk"],
        "geometry": route_details["geometry"],
        "road_names": route_details["road_names"],
        "instructions": route_details["instructions"],
    }

    # Update active navigation session with the new path
    update_session_with_new_route(
        trip_id=trip_id,
        new_geometry=route_details["geometry"],
        new_instructions=route_details["instructions"],
    )

    return new_route_payload

