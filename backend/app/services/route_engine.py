from pathlib import Path
import osmnx as ox
import networkx as nx

BASE_DIR = Path(__file__).resolve().parents[2]
GRAPH_CACHE = BASE_DIR / "artifacts" / "chennai_drive.graphml.xml"
if not GRAPH_CACHE.exists():
    GRAPH_CACHE = BASE_DIR / "artifacts" / "chennai_drive.graphml"

# Load Chennai driving network once when the backend starts.
if GRAPH_CACHE.exists():
    print(f"Loading Chennai road network from local cache: {GRAPH_CACHE.name}...")
    GRAPH = ox.load_graphml(str(GRAPH_CACHE))
else:
    print("Loading Chennai road network from OSM...")
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
    """Return the shortest driving route between two coordinates with resilient node fallbacks."""

    source_node = get_nearest_node(
        source_latitude,
        source_longitude,
    )

    destination_node = get_nearest_node(
        destination_latitude,
        destination_longitude,
    )

    try:
        route = nx.shortest_path(
            GRAPH,
            source_node,
            destination_node,
            weight="length",
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        # Resilient fallback: Try adjacent candidate nodes on navigable corridors
        src_candidates = [source_node]
        dst_candidates = [destination_node]

        if hasattr(GRAPH, "successors"):
            src_candidates.extend(list(GRAPH.successors(source_node))[:5])
        if hasattr(GRAPH, "predecessors"):
            dst_candidates.extend(list(GRAPH.predecessors(destination_node))[:5])

        route = None
        for s in src_candidates:
            for d in dst_candidates:
                try:
                    route = nx.shortest_path(GRAPH, s, d, weight="length")
                    source_node = s
                    destination_node = d
                    break
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue
            if route:
                break

        if not route:
            try:
                undirected_G = GRAPH.to_undirected(as_view=True)
                route = nx.shortest_path(undirected_G, source_node, destination_node, weight="length")
            except Exception:
                raise nx.NetworkXNoPath(
                    f"No navigable road path found between ({source_latitude:.4f}, {source_longitude:.4f}) and ({destination_latitude:.4f}, {destination_longitude:.4f})."
                )

    return {
        "source_node": source_node,
        "destination_node": destination_node,
        "route": route,
        "graph": GRAPH,
    }