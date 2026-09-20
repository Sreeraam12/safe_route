import pandas as pd

from backend.app.services.route_engine import GRAPH
from backend.app.services.candidate_route_engine import (
    generate_candidate_routes,
)
from backend.app.services.route_scoring import (
    score_candidate_routes,
)


risk_data = pd.read_pickle(
    "backend/artifacts/osm_hybrid_risk.pkl"
)

candidates = generate_candidate_routes(
    GRAPH,
    2271477981,
    310728484,
)

scored = score_candidate_routes(
    GRAPH,
    candidates,
    risk_data,
)


for route in scored:
    print(
        f"Route {route['route_index']:2d} | "
        f"{route['distance_km']:.3f} km | "
        f"Risk {route['route_risk']:.2f} | "
        f"Safety {route['safety_score']:.2f} | "
        f"Coverage {route['coverage_pct']:.1f}%"
    )