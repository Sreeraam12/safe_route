import osmnx as ox
import networkx as nx


# Load Chennai driving network once when the backend starts.
print("Loading Chennai road network...")

GRAPH = ox.graph_from_place(
    "Chennai, Tamil Nadu, India",
    network_type="drive",
    simplify=True,
)

print(
    f"Chennai road network loaded: "
    f"{len(GRAPH.nodes)} nodes, {len(GRAPH.edges)} edges"
)


def get_nearest_node(latitude: float, longitude: float):
    """Find the nearest OSM road node to a coordinate."""

    return ox.distance.nearest_nodes(
        GRAPH,
        X=longitude,
        Y=latitude,
    )


def get_shortest_route(
    source_latitude: float,
    source_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
):
    """Return the shortest driving route between two coordinates."""

    source_node = get_nearest_node(
        source_latitude,
        source_longitude,
    )

    destination_node = get_nearest_node(
        destination_latitude,
        destination_longitude,
    )

    route = nx.shortest_path(
        GRAPH,
        source_node,
        destination_node,
        weight="length",
    )

    return {
        "source_node": source_node,
        "destination_node": destination_node,
        "route": route,
        "graph": GRAPH,
    }