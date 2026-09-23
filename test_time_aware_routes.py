import asyncio
from datetime import datetime, date, time
import pandas as pd

from backend.app.services.route_engine import GRAPH
from backend.app.services.final_route_engine import calculate_final_route_scores

SOURCE_NODE = 2271477981
DESTINATION_NODE = 310728484

TEST_TIMES = [
    ("Morning (10:00 AM)", time(10, 0)),
    ("Afternoon (02:00 PM)", time(14, 0)),
    ("Evening (07:00 PM)", time(19, 0)),
    ("Late Night (11:30 PM)", time(23, 30)),
]

async def run_time_tests():
    risk_data = pd.read_pickle("backend/artifacts/osm_hybrid_risk.pkl")
    today = date(2026, 9, 23)

    print("\n" + "=" * 90)
    print("SAFEROUTE TIME-AWARE RISK COMPARISON TEST")
    print("=" * 90)

    for label, t in TEST_TIMES:
        dt = datetime.combine(today, t)
        routes = await calculate_final_route_scores(
            graph=GRAPH,
            source_node=SOURCE_NODE,
            destination_node=DESTINATION_NODE,
            risk_data=risk_data,
            travel_datetime=dt,
            num_candidates=20,
            top_k=5,
        )

        top = routes[0]
        print(f"\n--- {label} (Time: {t.strftime('%H:%M')}) ---")
        print(f"  Period:            {top.get('time_period')}")
        print(f"  Base Time Risk:    {top.get('time_risk'):.2f}")
        print(f"  Base Hybrid Risk:  {top.get('base_hybrid_risk'):.2f}")
        print(f"  Time-Aware Risk:   {top.get('hybrid_risk'):.2f}")
        print(f"  Traffic Risk:      {top.get('traffic_risk'):.2f}")
        print(f"  Final Risk:        {top.get('final_risk'):.2f}")
        print(f"  Final Safety:      {top.get('final_safety_score'):.2f}")

    print("\n" + "=" * 90)
    print("TIME-AWARE RISK TEST COMPLETE")
    print("=" * 90)

if __name__ == "__main__":
    asyncio.run(run_time_tests())

