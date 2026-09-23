import pandas as pd

from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.app.schemas.route import (
    GeocodeRequest,
    GeocodeResponse,
    RouteSearchRequest,
)

from backend.app.services.geocoder import (
    geocode_place,
)

from backend.app.services.route_engine import (
    get_shortest_route,
)

from backend.app.services.final_route_engine import (
    calculate_final_route_scores,
)

from backend.app.services.route_geometry import (
    build_route_details,
)


router = APIRouter(
    prefix="/api/routes",
    tags=["Routes"],
)


RISK_DATA = pd.read_pickle(
    "backend/artifacts/osm_hybrid_risk.pkl"
)


@router.post(
    "/geocode",
    response_model=GeocodeResponse,
)
async def geocode(
    request: GeocodeRequest,
):
    result = await geocode_place(
        request.place
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Place not found",
        )

    return result


from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Depends
from backend.app.db.session import get_db
from backend.app.api.deps import get_optional_user
from backend.app.models.user import User
from backend.app.services.personal_twin_engine import get_effective_twin_weights

@router.post("/search")
async def search_route(
    request: RouteSearchRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):

    source = await geocode_place(request.source)

    if source is None:
        raise HTTPException(
            status_code=404,
            detail=f"Source place not found: {request.source}",
        )

    destination = await geocode_place(request.destination)

    if destination is None:
        raise HTTPException(
            status_code=404,
            detail=f"Destination place not found: {request.destination}",
        )

    now = datetime.now()
    travel_date = request.travel_date or now.date()
    travel_time = request.travel_time or now.time().replace(second=0, microsecond=0)

    travel_datetime = datetime.combine(
        travel_date,
        travel_time,
    )

    route_data = get_shortest_route(
        source["latitude"],
        source["longitude"],
        destination["latitude"],
        destination["longitude"],
    )
    source_node = route_data["source_node"]
    destination_node = route_data["destination_node"]

    # -----------------------------------------------------
    # 4. Generate + score Top 5 routes
    # -----------------------------------------------------

    twin_weights = await get_effective_twin_weights(
        current_user.id if current_user else None,
        db,
    )

    ranked_routes = await calculate_final_route_scores(
        graph=route_data["graph"],
        source_node=source_node,
        destination_node=destination_node,
        risk_data=RISK_DATA,
        travel_datetime=travel_datetime,
        twin_weights=twin_weights,
        num_candidates=20,
        top_k=5,
    )

    # -----------------------------------------------------
    # 5. Add geometry + instructions
    # -----------------------------------------------------

    response_routes = []

    for rank, route in enumerate(
        ranked_routes,
        start=1,
    ):
        route_details = build_route_details(
            route_data["graph"],
            route["route"],
        )

        response_routes.append({
            "rank": rank,

            "route_index":
                route["route_index"],

            "distance_km":
                route_details["distance_km"],

            "final_risk":
                route["final_risk"],

            "safety_score":
                route["final_safety_score"],

            "personalized_risk":
                route.get("personalized_risk", route["final_risk"]),

            "personalized_safety_score":
                route.get("personalized_safety_score", route["final_safety_score"]),

            "personal_adjustment":
                route.get("personal_adjustment", 0.0),

            "hybrid_risk":
                route["hybrid_risk"],

            "hybrid_safety":
                route["hybrid_safety"],

            "base_hybrid_risk":
                route.get("base_hybrid_risk", route["hybrid_risk"]),

            "time_risk":
                route.get("time_risk", 0.0),

            "time_period":
                route.get("time_period", "normal"),

            "traffic_risk":
                route["traffic_risk"],

            "traffic_safety":
                route["traffic_safety"],

            "traffic_coverage_pct":
                route["traffic_coverage_pct"],

            "traffic_matched_segments":
                route[
                    "traffic_matched_segments"
                ],

            "traffic_total_segments":
                route[
                    "traffic_total_segments"
                ],

            "geometry":
                route_details["geometry"],

            "road_names":
                route_details["road_names"],

            "instructions":
                route_details["instructions"],
        })

    # -----------------------------------------------------
    # 6. Final response
    # -----------------------------------------------------

    return {
        "source": source,
        "destination": destination,

        "source_node": source_node,
        "destination_node": destination_node,

        "route_count": len(
            response_routes
        ),

        "routes": response_routes,
    }