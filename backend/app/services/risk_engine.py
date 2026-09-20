from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

HYBRID_RISK_PATH = (
    BASE_DIR
    / "artifacts"
    / "osm_hybrid_risk.pkl"
)


print("Loading SafeRoute risk data...")

RISK_DATA = pd.read_pickle(HYBRID_RISK_PATH)

print(
    f"SafeRoute risk data loaded: "
    f"{len(RISK_DATA)} segments"
)


def get_route_risk(graph, route):
    """
    Calculate risk for an OSM route using
    the cached SafeRoute hybrid-risk data.
    """

    route_segments = []

    for u, v in zip(route[:-1], route[1:]):

        edge_data = graph.get_edge_data(u, v)

        if edge_data is None:
            continue

        # Select the edge with the shortest length
        key = min(
            edge_data,
            key=lambda k: edge_data[k].get(
                "length",
                float("inf")
            ),
        )

        route_segments.append(
            {
                "u": u,
                "v": v,
                "key": key,
            }
        )

    if not route_segments:
        raise ValueError(
            "No valid road segments found for route."
        )

    route_df = pd.DataFrame(route_segments)

    risk_columns = [
        "osm_segment_id",
        "u",
        "v",
        "key",
        "length",
        "hybrid_risk_100",
        "hybrid_safety_score",
    ]

    risk_lookup = RISK_DATA[risk_columns].copy()

    merged = route_df.merge(
        risk_lookup,
        on=["u", "v", "key"],
        how="left",
    )

    # Check how many route segments have
    # SafeRoute risk data.
    matched = merged["hybrid_risk_100"].notna().sum()

    if matched == 0:
        raise ValueError(
            "No route segments matched SafeRoute risk data."
        )

    merged["hybrid_risk_100"] = (
        merged["hybrid_risk_100"]
        .fillna(merged["hybrid_risk_100"].mean())
    )

    merged["length"] = merged["length"].fillna(0)

    total_length = merged["length"].sum()

    if total_length <= 0:
        raise ValueError(
            "Route has invalid total length."
        )

    route_risk = (
        (
            merged["hybrid_risk_100"]
            * merged["length"]
        ).sum()
        / total_length
    )

    route_safety = 100.0 - route_risk

    return {
        "route_risk": float(route_risk),
        "safety_score": float(route_safety),
        "total_length_m": float(total_length),
        "matched_segments": int(matched),
        "total_segments": int(len(merged)),
    }