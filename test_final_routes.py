import asyncio
import pandas as pd

from backend.app.services.route_engine import GRAPH

from backend.app.services.final_route_engine import (
    calculate_final_route_scores,
)


SOURCE_NODE = 2271477981
DESTINATION_NODE = 310728484


async def main():

    print("\nLoading risk data...")

    risk_data = pd.read_pickle(
        "backend/artifacts/osm_hybrid_risk.pkl"
    )

    print(
        f"Risk segments: {len(risk_data)}"
    )

    print("\nCalculating final routes...")

    from datetime import datetime

    routes = await calculate_final_route_scores(
        graph=GRAPH,
        source_node=SOURCE_NODE,
        destination_node=DESTINATION_NODE,
        risk_data=risk_data,
        travel_datetime=datetime.now(),
        num_candidates=20,
        top_k=5,
    )

    print("\n")
    print("=" * 90)
    print("TOP 5 SAFEROUTE RESULTS")
    print("=" * 90)

    for rank, route in enumerate(
        routes,
        start=1,
    ):

        print(
            f"\nRank {rank}"
        )

        print(
            f"Route: "
            f"{route['route_index']}"
        )

        print(
            f"Distance: "
            f"{route['distance_km']:.3f} km"
        )

        print(
            f"Hybrid Risk: "
            f"{route['hybrid_risk']:.2f}"
        )

        print(
            f"Traffic Risk: "
            f"{route['traffic_risk']:.2f}"
        )

        print(
            f"Traffic Coverage: "
            f"{route['traffic_coverage_pct']:.1f}%"
        )

        print(
            f"Final Risk: "
            f"{route['final_risk']:.2f}"
        )

        print(
            f"Final Safety Score: "
            f"{route['final_safety_score']:.2f}"
        )


asyncio.run(main())