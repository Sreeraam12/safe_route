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


from datetime import datetime

async def fetch_traffic_point(point):
    traffic = await get_traffic(
        point["latitude"],
        point["longitude"],
    )

    return {
        **point,
        **traffic,
    }


from backend.app.services.time_risk_engine import calculate_time_context
from backend.app.services.personal_twin_engine import calculate_personalized_route_risk
from backend.app.services.route_geometry import get_route_segment_ids
from backend.app.services.segment_memory_service import evaluate_route_segment_memory

async def calculate_final_route_scores(
    graph,
    source_node,
    destination_node,
    risk_data,
    travel_datetime=None,
    twin_weights=None,
    segment_memories=None,
    num_candidates=20,
    top_k=5,
):
    if travel_datetime is None:
        travel_datetime = datetime.now()

    print(
        "[SafeRoute] Generating candidate routes...",
        flush=True,
    )

    candidates = generate_candidate_routes(
        graph,
        source_node,
        destination_node,
        segment_memories=segment_memories,
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
        travel_datetime=travel_datetime,
    )

    print(
        "[SafeRoute] Hybrid risk calculation complete.",
        flush=True,
    )

    final_routes = []
    time_ctx = calculate_time_context(travel_datetime)

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

        # Extract OSM segment IDs for this route
        route_seg_ids = get_route_segment_ids(graph, route)
        seg_memory_eval = evaluate_route_segment_memory(route_seg_ids, segment_memories or {})

        # Personal Twin calculation if user weights available or segment memory present
        personal_metrics = None
        if twin_weights or segment_memories:
            personal_metrics = calculate_personalized_route_risk(
                base_time_aware_risk=final_risk,
                matched_segments_df=matched_segments,
                twin_weights=twin_weights or {},
                time_context=time_ctx,
                segment_memory_eval=seg_memory_eval,
            )
            pers_risk = personal_metrics["personalized_risk"]
            pers_safety = personal_metrics["personalized_safety_score"]
        else:
            pers_risk = final_risk
            pers_safety = final_safety

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

            "base_hybrid_risk":
                route_data.get("base_hybrid_risk", hybrid_risk),

            "time_risk":
                route_data.get("time_risk", 0.0),

            "time_period":
                route_data.get("time_period", "normal"),

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

            "personalized_risk":
                pers_risk,

            "personalized_safety_score":
                pers_safety,

            "personal_adjustment":
                personal_metrics["personal_adjustment"] if personal_metrics else 0.0,

            "segment_memory_adjustment":
                personal_metrics["segment_memory_adjustment"] if personal_metrics else 0.0,

            "familiar_segments_count":
                personal_metrics["familiar_segments_count"] if personal_metrics else 0,

            "avoided_segments_count":
                personal_metrics["avoided_segments_count"] if personal_metrics else 0,

            "osm_segment_ids":
                route_seg_ids,

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
        key=lambda r: (
            -r["personalized_safety_score"],
            r["distance_km"],
        )
    )

    print(
        f"[SafeRoute] Returning top {top_k} routes.",
        flush=True,
    )

    return final_routes[:top_k]