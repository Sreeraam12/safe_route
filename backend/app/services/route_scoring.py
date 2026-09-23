from datetime import datetime
import pandas as pd


def get_route_edges(graph, route):
    """
    Convert a node route into OSM edge records.
    """

    edges = []

    for u, v in zip(route[:-1], route[1:]):
        edge_data = graph.get_edge_data(u, v)

        if edge_data is None:
            continue

        key = min(
            edge_data,
            key=lambda k: edge_data[k].get(
                "length",
                float("inf"),
            ),
        )

        edges.append(
            {
                "u": u,
                "v": v,
                "key": key,
            }
        )

    return pd.DataFrame(edges)


from backend.app.services.time_risk_engine import (
    calculate_time_context,
    compute_time_aware_segment_risk,
)

def score_route(
    graph,
    route,
    risk_data,
    travel_datetime=None,
):
    """
    Calculate distance-weighted, time-aware SafeRoute risk
    for one candidate route.
    """
    if travel_datetime is None:
        travel_datetime = datetime.now()

    route_edges = get_route_edges(
        graph,
        route,
    )

    if route_edges.empty:
        raise ValueError(
            "No valid edges found for route."
        )

    time_ctx = calculate_time_context(travel_datetime)

    available_env_cols = [
        col for col in ["lighting_score", "isolation_score", "crowd_score"]
        if col in risk_data.columns
    ]

    risk_columns = [
        "u",
        "v",
        "key",
        "osm_segment_id",
        "length",
        "hybrid_risk_100",
    ] + available_env_cols

    risk_lookup = risk_data[risk_columns].copy()

    merged = route_edges.merge(
        risk_lookup,
        on=["u", "v", "key"],
        how="left",
    )

    matched_segments = int(
        merged["hybrid_risk_100"].notna().sum()
    )

    total_segments = len(merged)

    if matched_segments == 0:
        raise ValueError(
            "No route segments matched SafeRoute risk data."
        )

    # Use OSM edge length for route weighting.
    merged["edge_length"] = merged.apply(
        lambda row: graph[row["u"]][row["v"]][row["key"]].get(
            "length",
            0.0,
        ),
        axis=1,
    )

    # Only matched segments contribute to the SafeRoute risk calculation.
    matched = merged[
        merged["hybrid_risk_100"].notna()
    ].copy()

    total_length = matched["edge_length"].sum()

    if total_length <= 0:
        raise ValueError(
            "Invalid route length."
        )

    # Compute time-aware contextual risk per segment
    matched["time_aware_risk_100"] = compute_time_aware_segment_risk(
        matched,
        time_ctx,
    )

    route_risk = (
        (
            matched["time_aware_risk_100"]
            * matched["edge_length"]
        ).sum()
        / total_length
    )

    base_hybrid_risk = (
        (
            matched["hybrid_risk_100"]
            * matched["edge_length"]
        ).sum()
        / total_length
    )

    route_risk = float(
        max(0.0, min(100.0, route_risk))
    )

    safety_score = 100.0 - route_risk

    return {
        "distance_km": float(
            total_length / 1000.0
        ),
        "route_risk": route_risk,
        "safety_score": float(safety_score),
        "base_hybrid_risk": float(base_hybrid_risk),
        "time_risk": float(time_ctx["base_time_risk"]),
        "time_period": time_ctx["period"],
        "matched_segments": matched_segments,
        "total_segments": total_segments,
        "coverage_pct": float(
            matched_segments
            / total_segments
            * 100.0
        ),
    }


def score_candidate_routes(
    graph,
    candidate_routes,
    risk_data,
    travel_datetime=None,
):
    """
    Score all candidate routes.
    """

    scored_routes = []

    for candidate in candidate_routes:

        score = score_route(
            graph,
            candidate["route"],
            risk_data,
            travel_datetime=travel_datetime,
        )

        scored_routes.append(
            {
                "route_index": candidate["route_index"],
                "route": candidate["route"],
                **score,
            }
        )

    return scored_routes