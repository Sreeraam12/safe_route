import os
import math
import httpx
import pandas as pd

from dotenv import load_dotenv

load_dotenv()


TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")

TOMTOM_FLOW_URL = (
    "https://api.tomtom.com/traffic/services/4/"
    "flowSegmentData/absolute/10/json"
)


# ---------------------------------------------------------
# TOMTOM TRAFFIC
# ---------------------------------------------------------

def parse_tomtom_traffic(response_json: dict) -> dict:
    data = response_json["flowSegmentData"]

    current_speed = float(data["currentSpeed"])
    free_flow_speed = float(data["freeFlowSpeed"])
    current_travel_time = float(data["currentTravelTime"])

    if free_flow_speed > 0:
        congestion_ratio = (
            1.0 - current_speed / free_flow_speed
        )
    else:
        congestion_ratio = 0.0

    congestion_ratio = max(
        0.0,
        min(1.0, congestion_ratio),
    )

    road_closure = bool(
        data.get("roadClosure", False)
    )

    traffic_risk = (
        100.0
        if road_closure
        else congestion_ratio * 100.0
    )

    return {
        "traffic_speed_kmph": current_speed,
        "free_flow_speed_kmph": free_flow_speed,
        "congestion_ratio": congestion_ratio,
        "travel_time_min": current_travel_time / 60.0,
        "confidence": float(data.get("confidence", 0)),
        "road_closure": road_closure,
        "traffic_risk_100": traffic_risk,
    }


async def get_traffic(
    latitude: float,
    longitude: float,
) -> dict:
    fallback_traffic = {
        "traffic_speed_kmph": 28.0,
        "free_flow_speed_kmph": 40.0,
        "congestion_ratio": 0.30,
        "travel_time_min": 1.5,
        "confidence": 0.85,
        "road_closure": False,
        "traffic_risk_100": 30.0,
    }
    if not TOMTOM_API_KEY:
        return fallback_traffic

    params = {
        "key": TOMTOM_API_KEY,
        "point": f"{latitude},{longitude}",
        "unit": "KMPH",
        "openLr": "false",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                TOMTOM_FLOW_URL,
                params=params,
                timeout=3.5,
            )
        response.raise_for_status()
        return parse_tomtom_traffic(response.json())
    except Exception:
        return fallback_traffic


# ---------------------------------------------------------
# DISTANCE
# ---------------------------------------------------------

def haversine_distance_m(
    lat1,
    lon1,
    lat2,
    lon2,
):
    earth_radius = 6371000.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    return (
        2
        * earth_radius
        * math.asin(math.sqrt(a))
    )


# ---------------------------------------------------------
# ROUTE SAMPLING
# ---------------------------------------------------------

def sample_route_points(
    graph,
    route,
    interval_m=500.0,
):
    """
    Sample points approximately every interval_m
    along an OSM route.
    """

    points = []

    accumulated_distance = 0.0
    next_sample = 0.0

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

        edge = edge_data[key]

        length = float(
            edge.get("length", 0.0)
        )

        x1 = float(graph.nodes[u]["x"])
        y1 = float(graph.nodes[u]["y"])

        x2 = float(graph.nodes[v]["x"])
        y2 = float(graph.nodes[v]["y"])

        while (
            next_sample
            <= accumulated_distance + length
        ):
            distance_into_edge = (
                next_sample
                - accumulated_distance
            )

            if length > 0:
                ratio = (
                    distance_into_edge
                    / length
                )
            else:
                ratio = 0.0

            ratio = max(
                0.0,
                min(1.0, ratio),
            )

            lon = x1 + (
                x2 - x1
            ) * ratio

            lat = y1 + (
                y2 - y1
            ) * ratio

            points.append({
                "latitude": lat,
                "longitude": lon,
                "distance_m": next_sample,
            })

            next_sample += interval_m

        accumulated_distance += length

    # Always include final route node
    final_node = route[-1]

    points.append({
        "latitude": float(
            graph.nodes[final_node]["y"]
        ),
        "longitude": float(
            graph.nodes[final_node]["x"]
        ),
        "distance_m": accumulated_distance,
    })

    return points


# ---------------------------------------------------------
# REMOVE DUPLICATE QUERY POINTS
# ---------------------------------------------------------

def deduplicate_points(
    points,
    min_distance_m=100.0,
):
    """
    Remove query points that are too close
    to an already selected point.
    """

    selected = []

    for point in points:

        is_duplicate = False

        for existing in selected:

            distance = haversine_distance_m(
                point["latitude"],
                point["longitude"],
                existing["latitude"],
                existing["longitude"],
            )

            if distance < min_distance_m:
                is_duplicate = True
                break

        if not is_duplicate:
            selected.append(point)

    return selected


# ---------------------------------------------------------
# MATCH TRAFFIC TO ROUTE SEGMENTS
# ---------------------------------------------------------

def match_traffic_to_route(
    graph,
    route,
    traffic_observations,
    max_distance_m=100.0,
):
    """
    Match TomTom observations to OSM route edges.
    """

    matched_segments = []

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

        node_u = graph.nodes[u]
        node_v = graph.nodes[v]

        edge_lat = (
            float(node_u["y"])
            + float(node_v["y"])
        ) / 2.0

        edge_lon = (
            float(node_u["x"])
            + float(node_v["x"])
        ) / 2.0

        closest_observation = None
        closest_distance = float("inf")

        for observation in traffic_observations:

            distance = haversine_distance_m(
                edge_lat,
                edge_lon,
                observation["latitude"],
                observation["longitude"],
            )

            if distance < closest_distance:
                closest_distance = distance
                closest_observation = observation

        matched = (
            closest_observation is not None
            and closest_distance <= max_distance_m
        )

        segment = {
            "u": u,
            "v": v,
            "key": key,
            "length": float(
                edge_data[key].get(
                    "length",
                    0.0,
                )
            ),
            "traffic_matched": matched,
            "traffic_match_distance_m": (
                float(closest_distance)
                if closest_observation
                else None
            ),
        }

        if matched:
            segment.update({
                "traffic_speed_kmph":
                    closest_observation[
                        "traffic_speed_kmph"
                    ],
                "free_flow_speed_kmph":
                    closest_observation[
                        "free_flow_speed_kmph"
                    ],
                "congestion_ratio":
                    closest_observation[
                        "congestion_ratio"
                    ],
                "travel_time_min":
                    closest_observation[
                        "travel_time_min"
                    ],
                "confidence":
                    closest_observation[
                        "confidence"
                    ],
                "road_closure":
                    closest_observation[
                        "road_closure"
                    ],
                "traffic_risk_100":
                    closest_observation[
                        "traffic_risk_100"
                    ],
            })

        matched_segments.append(segment)

    return pd.DataFrame(matched_segments)


# ---------------------------------------------------------
# ROUTE TRAFFIC RISK
# ---------------------------------------------------------

def calculate_route_traffic_risk(
    matched_segments,
):
    if matched_segments.empty:
        raise ValueError(
            "No route segments available."
        )

    total_segments = len(
        matched_segments
    )

    matched = matched_segments[
        matched_segments["traffic_matched"]
    ].copy()

    matched_segments_count = len(matched)

    if matched_segments_count == 0:
        return {
            "traffic_risk_100": 0.0,
            "traffic_safety_score": 100.0,
            "traffic_coverage_pct": 0.0,
            "matched_segments": 0,
            "total_segments": total_segments,
        }

    total_length = matched["length"].sum()

    if total_length <= 0:
        raise ValueError(
            "Invalid route segment lengths."
        )

    traffic_risk = (
        (
            matched["traffic_risk_100"]
            * matched["length"]
        ).sum()
        / total_length
    )

    traffic_risk = max(
        0.0,
        min(100.0, float(traffic_risk)),
    )

    return {
        "traffic_risk_100": traffic_risk,
        "traffic_safety_score":
            100.0 - traffic_risk,
        "traffic_coverage_pct":
            (
                matched_segments_count
                / total_segments
                * 100.0
            ),
        "matched_segments":
            matched_segments_count,
        "total_segments":
            total_segments,
    }