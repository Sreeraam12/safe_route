import asyncio
import pandas as pd

from backend.app.services.route_engine import GRAPH
from backend.app.services.candidate_route_engine import (
    generate_candidate_routes,
)
from backend.app.services.traffic_engine import (
    sample_route_points,
    deduplicate_points,
    get_traffic,
    match_traffic_to_route,
    calculate_route_traffic_risk,
)


SOURCE_NODE = 2271477981
DESTINATION_NODE = 310728484


async def main():

    candidates = generate_candidate_routes(
        GRAPH,
        SOURCE_NODE,
        DESTINATION_NODE,
        num_candidates=1,
    )

    route = candidates[0]["route"]

    print(
        f"Route distance: "
        f"{candidates[0]['distance_km']:.3f} km"
    )

    points = sample_route_points(
        GRAPH,
        route,
        interval_m=500.0,
    )

    print(
        f"Sample points: {len(points)}"
    )

    query_points = deduplicate_points(
        points,
        min_distance_m=100.0,
    )

    print(
        f"Unique TomTom queries: "
        f"{len(query_points)}"
    )

    traffic_observations = []

    for index, point in enumerate(query_points):

        print(
            f"Querying TomTom "
            f"{index + 1}/{len(query_points)}..."
        )

        traffic = await get_traffic(
            point["latitude"],
            point["longitude"],
        )

        traffic_observations.append({
            **point,
            **traffic,
        })

    matched_segments = match_traffic_to_route(
        GRAPH,
        route,
        traffic_observations,
        max_distance_m=100.0,
    )

    result = calculate_route_traffic_risk(
        matched_segments
    )

    print("\nRoute Traffic Result")
    print("-------------------------")

    for key, value in result.items():
        print(f"{key}: {value}")


asyncio.run(main())