"""
SafeRoute GPS Map Matcher
=========================
Projects live GPS coordinates onto the planned route linestring, determines
current progress, cross-track error (deviation in meters), and nearest segment.

Conforms to SafeRoute Final Architecture Roadmap (Sections 53D, 53E).
"""

import math
from typing import List, Tuple, Dict, Any


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance between two coordinates in meters."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    return 2.0 * r * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def project_point_onto_segment(
    p_lat: float, p_lon: float,
    a_lat: float, a_lon: float,
    b_lat: float, b_lon: float,
) -> Tuple[float, float, float]:
    """
    Project point P onto segment AB using equirectangular approximation.
    Returns: (proj_lat, proj_lon, distance_in_meters_from_P)
    """
    mean_lat = math.radians((a_lat + b_lat) / 2.0)
    cos_lat = math.cos(mean_lat)

    # Convert lat/lon deltas to meters approx
    def to_xy(lat: float, lon: float):
        x = math.radians(lon) * cos_lat * 6371000.0
        y = math.radians(lat) * 6371000.0
        return x, y

    px, py = to_xy(p_lat, p_lon)
    ax, ay = to_xy(a_lat, a_lon)
    bx, by = to_xy(b_lat, b_lon)

    dx = bx - ax
    dy = by - ay
    seg_len_sq = dx * dx + dy * dy

    if seg_len_sq < 1e-6:
        # Segment is essentially a single point
        d = haversine_distance_m(p_lat, p_lon, a_lat, a_lon)
        return a_lat, a_lon, d

    # Projection factor t in [0.0, 1.0]
    t = ((px - ax) * dx + (py - ay) * dy) / seg_len_sq
    t = max(0.0, min(1.0, t))

    proj_lat = a_lat + t * (b_lat - a_lat)
    proj_lon = a_lon + t * (b_lon - a_lon)

    dist_m = haversine_distance_m(p_lat, p_lon, proj_lat, proj_lon)
    return proj_lat, proj_lon, dist_m


def match_gps_to_route(
    gps_lat: float,
    gps_lon: float,
    route_geometry: List[List[float]],  # [[lon, lat], [lon, lat], ...]
) -> Dict[str, Any]:
    """
    Match GPS location to the route polyline.

    Returns:
    - min_distance_m: cross-track error to nearest route point
    - nearest_segment_index: index of the segment [i, i+1]
    - matched_coords: [lat, lon] of projected point
    - distance_along_route_m: accumulated distance along route up to projection
    - total_route_distance_m: total route length
    """
    if len(route_geometry) < 2:
        return {
            "min_distance_m": 0.0,
            "nearest_segment_index": 0,
            "matched_coords": [gps_lat, gps_lon],
            "distance_along_route_m": 0.0,
            "total_route_distance_m": 0.0,
        }

    min_dist = float("inf")
    best_segment_idx = 0
    best_proj = (gps_lat, gps_lon)
    best_seg_cum_dist = 0.0

    cum_dist = 0.0
    segment_lengths = []

    for i in range(len(route_geometry) - 1):
        a_lon, a_lat = route_geometry[i]
        b_lon, b_lat = route_geometry[i + 1]

        seg_len = haversine_distance_m(a_lat, a_lon, b_lat, b_lon)
        segment_lengths.append(seg_len)

        p_lat, p_lon, dist_m = project_point_onto_segment(
            gps_lat, gps_lon, a_lat, a_lon, b_lat, b_lon
        )

        if dist_m < min_dist:
            min_dist = dist_m
            best_segment_idx = i
            best_proj = (p_lat, p_lon)
            # Distance along this segment to projection
            along_seg = haversine_distance_m(a_lat, a_lon, p_lat, p_lon)
            best_seg_cum_dist = cum_dist + along_seg

        cum_dist += seg_len

    return {
        "min_distance_m": round(min_dist, 1),
        "nearest_segment_index": best_segment_idx,
        "matched_coords": [round(best_proj[0], 6), round(best_proj[1], 6)],
        "distance_along_route_m": round(best_seg_cum_dist, 1),
        "total_route_distance_m": round(cum_dist, 1),
        "remaining_distance_m": max(0.0, round(cum_dist - best_seg_cum_dist, 1)),
    }

