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


def score_route(graph, route, risk_data):
    """
    Calculate distance-weighted SafeRoute risk
    for one candidate route.
    """

    route_edges = get_route_edges(
        graph,
        route,
    )

    if route_edges.empty:
        raise ValueError(
            "No valid edges found for route."
        )

    risk_columns = [
        "u",
        "v",
        "key",
        "osm_segment_id",
        "length",
        "hybrid_risk_100",
    ]

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

    # Only matched segments contribute to the
    # SafeRoute risk calculation.
    matched = merged[
        merged["hybrid_risk_100"].notna()
    ].copy()

    total_length = matched["edge_length"].sum()

    if total_length <= 0:
        raise ValueError(
            "Invalid route length."
        )

    route_risk = (
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
        )

        scored_routes.append(
            {
                "route_index": candidate["route_index"],
                "route": candidate["route"],
                **score,
            }
        )

    return scored_routes