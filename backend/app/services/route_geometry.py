import math


def get_edge_data(graph, u, v):
    """
    Return the shortest parallel edge between two nodes.
    """
    edge_data = graph.get_edge_data(u, v)

    if edge_data is None:
        return None

    if graph.is_multigraph():
        return min(
            edge_data.values(),
            key=lambda data: float(data.get("length", 0.0)),
        )

    return edge_data


def get_route_distance(graph, route):
    """
    Calculate total route distance in meters.
    """
    total_distance = 0.0

    for u, v in zip(route[:-1], route[1:]):
        data = get_edge_data(graph, u, v)

        if data:
            total_distance += float(data.get("length", 0.0))

    return total_distance


def get_road_name(graph, u, v):
    """
    Get a clean road name for an edge.
    """
    data = get_edge_data(graph, u, v)

    if not data:
        return "Unnamed road"

    name = data.get("name")

    if isinstance(name, list):
        name = name[0] if name else None

    if not name:
        return "Unnamed road"

    return str(name)


def get_segment_id(data, u, v):
    if not data:
        return f"{u}_{v}"
    osmid = data.get("osmid")
    if osmid:
        if isinstance(osmid, list):
            return str(osmid[0])
        elif isinstance(osmid, str) and osmid.startswith("["):
            clean = osmid.strip("[]'\" ").split(",")[0].strip(" '\"")
            if clean:
                return clean
        return str(osmid)
    return f"{u}_{v}"


def get_route_segment_ids(graph, route):
    """
    Return unique ordered list of OSM segment IDs traversed by the route.
    """
    segment_ids = []
    seen = set()
    for u, v in zip(route[:-1], route[1:]):
        data = get_edge_data(graph, u, v)
        seg_id = get_segment_id(data, u, v)
        if seg_id not in seen:
            seen.add(seg_id)
            segment_ids.append(seg_id)
    return segment_ids


def get_road_names(graph, route):
    """
    Return unique consecutive road names.
    """
    names = []

    for u, v in zip(route[:-1], route[1:]):
        name = get_road_name(graph, u, v)

        if not names or names[-1] != name:
            names.append(name)

    return names


def get_route_geometry(graph, route):
    """
    Build route geometry using OSM edge geometry where available.

    Returns [longitude, latitude] coordinates.
    """
    geometry = []

    for u, v in zip(route[:-1], route[1:]):
        data = get_edge_data(graph, u, v)

        if not data:
            continue

        edge_geometry = data.get("geometry")

        if edge_geometry is not None:
            coords = list(edge_geometry.coords)

            # OSM geometry is usually (lon, lat)
            for lon, lat in coords:
                point = [float(lon), float(lat)]

                if not geometry or geometry[-1] != point:
                    geometry.append(point)

        else:
            # Fallback to node coordinates
            u_data = graph.nodes[u]
            v_data = graph.nodes[v]

            u_point = [
                float(u_data["x"]),
                float(u_data["y"]),
            ]

            v_point = [
                float(v_data["x"]),
                float(v_data["y"]),
            ]

            if not geometry or geometry[-1] != u_point:
                geometry.append(u_point)

            if geometry[-1] != v_point:
                geometry.append(v_point)

    return geometry


def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Calculate compass bearing from point 1 to point 2.
    """
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lon = math.radians(lon2 - lon1)

    x = math.sin(delta_lon) * math.cos(lat2)

    y = (
        math.cos(lat1) * math.sin(lat2)
        - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
    )

    bearing = math.degrees(math.atan2(x, y))

    return (bearing + 360) % 360


def bearing_to_direction(bearing):
    """
    Convert bearing to compass direction.
    """
    directions = [
        "north",
        "northeast",
        "east",
        "southeast",
        "south",
        "southwest",
        "west",
        "northwest",
    ]

    index = int((bearing + 22.5) // 45) % 8

    return directions[index]


def normalize_angle(angle):
    """
    Normalize angle to [-180, 180].
    """
    while angle > 180:
        angle -= 360

    while angle < -180:
        angle += 360

    return angle


def get_node_coordinates(graph, node):
    """
    Return node coordinates as latitude, longitude.
    """
    data = graph.nodes[node]

    return (
        float(data["y"]),
        float(data["x"]),
    )


def get_turn_type(angle):
    """
    Convert turn angle into a navigation instruction.
    """
    angle = normalize_angle(angle)

    if abs(angle) < 25:
        return "continue"

    if 25 <= angle < 60:
        return "slight right"

    if 60 <= angle < 135:
        return "right"

    if angle >= 135:
        return "sharp right"

    if -60 < angle <= -25:
        return "slight left"

    if -135 < angle <= -60:
        return "left"

    return "sharp left"


def format_distance(distance_m):
    """
    Format distance for human-readable navigation.
    """
    if distance_m < 1000:
        return f"{round(distance_m)} m"

    return f"{distance_m / 1000:.1f} km"


def build_navigation_segments(graph, route):
    """
    Group consecutive route edges by road name.

    Tiny unnamed/name-transition segments are merged into
    the surrounding navigation segment where possible.
    """
    segments = []

    for u, v in zip(route[:-1], route[1:]):
        data = get_edge_data(graph, u, v)

        if not data:
            continue

        distance = float(data.get("length", 0.0))
        name = get_road_name(graph, u, v)

        start_lat, start_lon = get_node_coordinates(graph, u)
        end_lat, end_lon = get_node_coordinates(graph, v)

        bearing = calculate_bearing(
            start_lat,
            start_lon,
            end_lat,
            end_lon,
        )

        if segments and segments[-1]["road_name"] == name:
            segments[-1]["distance_m"] += distance
            segments[-1]["end_node"] = v
            segments[-1]["end_bearing"] = bearing

        else:
            segments.append(
                {
                    "road_name": name,
                    "distance_m": distance,
                    "start_node": u,
                    "end_node": v,
                    "start_bearing": bearing,
                    "end_bearing": bearing,
                }
            )

    # Remove/merge very small road-name transitions.
    cleaned = []

    for segment in segments:
        if (
            cleaned
            and segment["distance_m"] < 30
            and segment["road_name"] == "Unnamed road"
        ):
            cleaned[-1]["distance_m"] += segment["distance_m"]
            cleaned[-1]["end_node"] = segment["end_node"]
            cleaned[-1]["end_bearing"] = segment["end_bearing"]
        else:
            cleaned.append(segment)

    return cleaned


def generate_route_instructions(graph, route):
    """
    Generate navigation-friendly turn-by-turn instructions.

    - Groups consecutive edges on the same road.
    - Detects meaningful turns.
    - Adds distance-based continue instructions.
    - Avoids noisy tiny road transitions.
    """

    segments = build_navigation_segments(graph, route)

    if not segments:
        return []

    instructions = []
    step_number = 1

    # ---------------------------------------------------------
    # First instruction
    # ---------------------------------------------------------

    first = segments[0]

    direction = bearing_to_direction(first["start_bearing"])

    instructions.append(
        {
            "step": step_number,
            "instruction": f"Head {direction} on {first['road_name']}",
            "distance_m": round(first["distance_m"], 1),
            "distance": format_distance(first["distance_m"]),
        }
    )

    step_number += 1

    # ---------------------------------------------------------
    # Process subsequent road segments
    # ---------------------------------------------------------

    for previous, current in zip(segments[:-1], segments[1:]):

        angle = normalize_angle(
            current["start_bearing"]
            - previous["end_bearing"]
        )

        turn_type = get_turn_type(angle)

        # Ignore extremely small segments.
        if current["distance_m"] < 30:
            continue

        # -----------------------------------------------------
        # Meaningful turn
        # -----------------------------------------------------

        if turn_type != "continue":

            instructions.append(
                {
                    "step": step_number,
                    "instruction": (
                        f"Turn {turn_type} "
                        f"onto {current['road_name']}"
                    ),
                    "distance_m": round(
                        current["distance_m"],
                        1,
                    ),
                    "distance": format_distance(
                        current["distance_m"]
                    ),
                }
            )

            step_number += 1

        # -----------------------------------------------------
        # Same direction / continuation
        # -----------------------------------------------------

        else:

            # Only add continuation instructions for
            # reasonably long segments.
            if current["distance_m"] >= 150:

                instructions.append(
                    {
                        "step": step_number,
                        "instruction": (
                            f"Continue on "
                            f"{current['road_name']}"
                        ),
                        "distance_m": round(
                            current["distance_m"],
                            1,
                        ),
                        "distance": format_distance(
                            current["distance_m"]
                        ),
                    }
                )

                step_number += 1

    # ---------------------------------------------------------
    # Destination
    # ---------------------------------------------------------

    instructions.append(
        {
            "step": step_number,
            "instruction": "Arrive at your destination",
            "distance_m": 0,
            "distance": "0 m",
        }
    )

    return instructions


def build_route_details(graph, route):
    """
    Build all frontend-ready route information.
    """
    distance_m = get_route_distance(graph, route)

    return {
        "geometry": get_route_geometry(graph, route),
        "distance_km": round(distance_m / 1000, 3),
        "road_names": get_road_names(graph, route),
        "osm_segment_ids": get_route_segment_ids(graph, route),
        "instructions": generate_route_instructions(
            graph,
            route,
        ),
    }