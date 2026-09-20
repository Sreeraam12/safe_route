import asyncio
import pandas as pd

from backend.app.services.candidate_route_engine import (
    generate_candidate_routes,
)

from backend.app.services.route_scoring import (
    score_candidate_routes,
)

from backend.app.services.traffic_engine import (
    sample_route_points,
    deduplicate_points,
    get_traffic,
    match_traffic_to_route,
    calculate_route_traffic_risk,
)


async def fetch_traffic_point(point):
    traffic = await get_traffic(
        point["latitude"],
        point["longitude"],
    )

    return {
        **point,
        **traffic,
    }


async def calculate_final_route_scores(
    graph,
    source_node,
    destination_node,
    risk_data,
    num_candidates=20,
    top_k=5,
):

    print(
        "[SafeRoute] Generating candidate routes...",
        flush=True,
    )

    candidates = generate_candidate_routes(
        graph,
        source_node,
        destination_node,
        num_candidates=num_candidates,
    )

    print(
        f"[SafeRoute] Generated "
        f"{len(candidates)} candidate routes.",
        flush=True,
    )

    print(
        "[SafeRoute] Calculating hybrid risk...",
        flush=True,
    )

    scored_routes = score_candidate_routes(
        graph,
        candidates,
        risk_data,
    )

    print(
        "[SafeRoute] Hybrid risk calculation complete.",
        flush=True,
    )

    final_routes = []

    for route_number, route_data in enumerate(
        scored_routes,
        start=1,
    ):

        route = route_data["route"]

        print(
            f"[SafeRoute] Traffic processing "
            f"route {route_number}/"
            f"{len(scored_routes)}...",
            flush=True,
        )

        sample_points = sample_route_points(
            graph,
            route,
            interval_m=500.0,
        )

        query_points = deduplicate_points(
            sample_points,
            min_distance_m=100.0,
        )

        print(
            f"[SafeRoute] Route {route_number}: "
            f"{len(query_points)} TomTom queries",
            flush=True,
        )

        # Run TomTom requests concurrently
        traffic_observations = await asyncio.gather(
            *[
                fetch_traffic_point(point)
                for point in query_points
            ]
        )

        matched_segments = match_traffic_to_route(
            graph,
            route,
            traffic_observations,
            max_distance_m=100.0,
        )

        traffic_result = calculate_route_traffic_risk(
            matched_segments
        )

        hybrid_risk = route_data["route_risk"]

        traffic_risk = traffic_result[
            "traffic_risk_100"
        ]

        final_risk = (
            0.90 * hybrid_risk
            + 0.10 * traffic_risk
        )

        final_risk = max(
            0.0,
            min(100.0, final_risk),
        )

        final_safety = 100.0 - final_risk

        final_routes.append({
            "route_index":
                route_data["route_index"],

            "route":
                route,

            "distance_km":
                route_data["distance_km"],

            "hybrid_risk":
                hybrid_risk,

            "hybrid_safety":
                route_data["safety_score"],

            "traffic_risk":
                traffic_risk,

            "traffic_safety":
                traffic_result[
                    "traffic_safety_score"
                ],

            "traffic_coverage_pct":
                traffic_result[
                    "traffic_coverage_pct"
                ],

            "traffic_matched_segments":
                traffic_result[
                    "matched_segments"
                ],

            "traffic_total_segments":
                traffic_result[
                    "total_segments"
                ],

            "final_risk":
                final_risk,

            "final_safety_score":
                final_safety,

            "risk_coverage_pct":
                route_data[
                    "coverage_pct"
                ],
        })

    print(
        "[SafeRoute] Sorting final routes...",
        flush=True,
    )

    final_routes.sort(
        key=lambda route: (
            -route["final_safety_score"],
            route["distance_km"],
        )
    )

    print(
        f"[SafeRoute] Returning top {top_k} routes.",
        flush=True,
    )

    return final_routes[:top_k]