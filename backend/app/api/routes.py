import pandas as pd

from fastapi import APIRouter, HTTPException

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


@router.post("/search")
async def search_route(
    request: RouteSearchRequest,
):
    # -----------------------------------------------------
    # 1. Geocode source
    # -----------------------------------------------------

    source = await geocode_place(
        request.source
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Source place not found: "
                f"{request.source}"
            ),
        )

    # -----------------------------------------------------
    # 2. Geocode destination
    # -----------------------------------------------------

    destination = await geocode_place(
        request.destination
    )

    if destination is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Destination place not found: "
                f"{request.destination}"
            ),
        )

    # -----------------------------------------------------
    # 3. Find nearest OSM nodes
    # -----------------------------------------------------

    route_data = get_shortest_route(
        source["latitude"],
        source["longitude"],
        destination["latitude"],
        destination["longitude"],
    )

    source_node = route_data[
        "source_node"
    ]

    destination_node = route_data[
        "destination_node"
    ]

    # -----------------------------------------------------
    # 4. Generate + score Top 5 routes
    # -----------------------------------------------------

    ranked_routes = (
        await calculate_final_route_scores(
            graph=route_data["graph"],
            source_node=source_node,
            destination_node=destination_node,
            risk_data=RISK_DATA,
            num_candidates=20,
            top_k=5,
        )
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

            "hybrid_risk":
                route["hybrid_risk"],

            "hybrid_safety":
                route["hybrid_safety"],

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