import networkx as nx


# Cache the simplified graph so we don't rebuild it
# for every route-search request.
_SIMPLE_GRAPH = None


def build_simple_graph(graph):
    """
    Convert OSM MultiDiGraph -> DiGraph.

    For parallel edges between the same nodes, keep
    the edge with the shortest distance.
    """

    simple_graph = nx.DiGraph()

    for u, v, data in graph.edges(data=True):
        length = float(
            data.get("length", 0.0)
        )

        if (
            not simple_graph.has_edge(u, v)
            or length < simple_graph[u][v]["length"]
        ):
            simple_graph.add_edge(
                u,
                v,
                length=length,
            )

    return simple_graph


def get_simple_graph(graph):
    """
    Build the simplified graph only once.
    """

    global _SIMPLE_GRAPH

    if _SIMPLE_GRAPH is None:
        print(
            "[SafeRoute] Building simplified route graph...",
            flush=True,
        )

        _SIMPLE_GRAPH = build_simple_graph(graph)

        print(
            f"[SafeRoute] Simplified graph ready: "
            f"{len(_SIMPLE_GRAPH.nodes)} nodes, "
            f"{len(_SIMPLE_GRAPH.edges)} edges",
            flush=True,
        )

    return _SIMPLE_GRAPH


def route_distance(graph, route):
    """Calculate total route distance in meters."""

    total_distance = 0.0

    for u, v in zip(route[:-1], route[1:]):
        edge_data = graph.get_edge_data(u, v)

        if edge_data is None:
            continue

        # Works with both MultiDiGraph and DiGraph.
        if isinstance(graph, nx.MultiDiGraph):
            key = min(
                edge_data,
                key=lambda k: edge_data[k].get(
                    "length",
                    float("inf"),
                ),
            )

            total_distance += float(
                edge_data[key].get("length", 0.0)
            )

        else:
            total_distance += float(
                edge_data.get("length", 0.0)
            )

    return total_distance


def route_similarity(route_a, route_b):
    """Calculate Jaccard similarity between two routes."""

    edges_a = set(
        zip(route_a[:-1], route_a[1:])
    )

    edges_b = set(
        zip(route_b[:-1], route_b[1:])
    )

    if not edges_a or not edges_b:
        return 0.0

    return len(edges_a & edges_b) / len(
        edges_a | edges_b
    )


def generate_candidate_routes(
    graph,
    source_node,
    destination_node,
    num_candidates=20,
    max_overlap=0.90,
    max_distance_factor=1.45,
):
    """
    Generate diverse candidate routes using iterative
    edge penalization.

    Each accepted route increases the cost of its edges,
    encouraging subsequent routes to use different roads.
    """

    simple_graph = get_simple_graph(graph)

    print(
        "[SafeRoute] Finding shortest route...",
        flush=True,
    )

    try:
        shortest_route = nx.shortest_path(
            simple_graph,
            source_node,
            destination_node,
            weight="length",
        )

    except nx.NetworkXNoPath:
        # Fallback 1: Try adjacent navigable nodes in case source or destination is a one-way dead end
        src_candidates = [source_node]
        dst_candidates = [destination_node]
        if hasattr(simple_graph, "successors"):
            src_candidates.extend(list(simple_graph.successors(source_node))[:10])
        if hasattr(simple_graph, "predecessors"):
            dst_candidates.extend(list(simple_graph.predecessors(destination_node))[:10])

        route_found = None
        for s in src_candidates:
            for d in dst_candidates:
                try:
                    route_found = nx.shortest_path(simple_graph, s, d, weight="length")
                    source_node = s
                    destination_node = d
                    break
                except nx.NetworkXNoPath:
                    continue
            if route_found:
                break

        if route_found:
            shortest_route = route_found
        else:
            # Fallback 2: Try undirected graph view
            try:
                undirected_simple = simple_graph.to_undirected(as_view=True)
                shortest_route = nx.shortest_path(
                    undirected_simple,
                    source_node,
                    destination_node,
                    weight="length",
                )
            except Exception:
                raise ValueError(
                    "No driving route exists between the selected locations."
                )

    shortest_distance = route_distance(
        simple_graph,
        shortest_route,
    )

    max_allowed_distance = (
        shortest_distance * max_distance_factor
    )

    print(
        f"[SafeRoute] Shortest route: "
        f"{shortest_distance / 1000:.2f} km",
        flush=True,
    )

    print(
        f"[SafeRoute] Candidate distance limit: "
        f"{max_allowed_distance / 1000:.2f} km",
        flush=True,
    )

    # Work on a copy so the cached graph is never modified.
    working_graph = simple_graph.copy()

    for u, v, data in working_graph.edges(data=True):
        data["route_cost"] = max(
            float(data.get("length", 0.0)),
            1.0,
    )

    candidate_routes = []

    for candidate_number in range(num_candidates):

        try:
            route = nx.shortest_path(
                working_graph,
                source_node,
                destination_node,
                weight="route_cost",
            )

        except nx.NetworkXNoPath:
            print(
                "[SafeRoute] No more alternative paths.",
                flush=True,
            )
            break

        distance_m = route_distance(
            simple_graph,
            route,
        )

        # Do not accept routes that are excessively longer
        # than the original shortest route.
        if distance_m > max_allowed_distance:
            print(
                f"[SafeRoute] Candidate "
                f"{candidate_number + 1} exceeds "
                f"distance limit.",
                flush=True,
            )
            break

        too_similar = any(
            route_similarity(
                route,
                existing,
            ) >= max_overlap
            for existing in candidate_routes
        )

        if too_similar:
            # Stronger penalty for the current route so that
            # the next iteration is pushed toward another road.
            for u, v in zip(
                route[:-1],
                route[1:],
            ):
                if working_graph.has_edge(u, v):
                    working_graph[u][v]["route_cost"] *= 1.5

            continue

        candidate_routes.append(route)

        print(
            f"[SafeRoute] Candidate "
            f"{len(candidate_routes)} accepted "
            f"({distance_m / 1000:.2f} km)",
            flush=True,
        )

        # Penalize every edge used by this route.
        #
        # Longer penalty = stronger encouragement to
        # find another road.
        for u, v in zip(
            route[:-1],
            route[1:],
        ):
            if working_graph.has_edge(u, v):
                working_graph[u][v]["route_cost"] *= 1.35

        if len(candidate_routes) >= num_candidates:
            break

    print(
        f"[SafeRoute] Generated "
        f"{len(candidate_routes)} candidate routes.",
        flush=True,
    )

    if not candidate_routes:
        raise ValueError(
            "Could not generate candidate routes."
        )

    candidates = []

    for index, route in enumerate(candidate_routes):

        distance_m = route_distance(
            simple_graph,
            route,
        )

        candidates.append(
            {
                "route_index": index,
                "route": route,
                "distance_m": distance_m,
                "distance_km": distance_m / 1000.0,
            }
        )

    return candidates