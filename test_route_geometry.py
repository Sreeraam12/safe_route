from backend.app.services.route_engine import GRAPH

from backend.app.services.candidate_route_engine import (
    generate_candidate_routes,
)

from backend.app.services.route_geometry import (
    build_route_details,
)


SOURCE_NODE = 2271477981
DESTINATION_NODE = 310728484


candidates = generate_candidate_routes(
    GRAPH,
    SOURCE_NODE,
    DESTINATION_NODE,
    num_candidates=1,
)

route = candidates[0]["route"]

details = build_route_details(
    GRAPH,
    route,
)


print("\nRoute Geometry")
print("=" * 60)

print(
    f"Distance: "
    f"{details['distance_km']:.3f} km"
)

print(
    f"Geometry points: "
    f"{len(details['geometry'])}"
)

print("\nGeometry:")
print(
    details["geometry"][:5]
)

print("\nRoad names:")
for road in details["road_names"]:
    print(
        f"  {road}"
    )

print("\nInstructions:")
for instruction in details["instructions"]:
    print(
        f"{instruction['step']}. "
        f"{instruction['instruction']}"
    )