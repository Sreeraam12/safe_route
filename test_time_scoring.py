from datetime import datetime, date, time
import pandas as pd

from backend.app.services.route_engine import GRAPH
from backend.app.services.candidate_route_engine import generate_candidate_routes
from backend.app.services.route_scoring import score_candidate_routes

SOURCE_NODE = 2271477981
DESTINATION_NODE = 310728484

def test_time_variation():
    print("Loading risk data...")
    risk_data = pd.read_pickle("backend/artifacts/osm_hybrid_risk.pkl")

    print("Generating candidate routes...")
    candidates = generate_candidate_routes(
        GRAPH,
        SOURCE_NODE,
        DESTINATION_NODE,
        num_candidates=4,
    )

    test_times = [
        ("Morning", time(10, 0)),
        ("Afternoon", time(14, 0)),
        ("Evening", time(19, 0)),
        ("Late Night", time(23, 30)),
    ]

    results = {}
    today = date(2026, 9, 23)

    print("\n" + "=" * 80)
    print("TIME-AWARE SCORING VERIFICATION")
    print("=" * 80)

    for label, t in test_times:
        dt = datetime.combine(today, t)
        scored = score_candidate_routes(
            GRAPH,
            candidates,
            risk_data,
            travel_datetime=dt,
        )
        results[label] = scored
        top = scored[0]
        print(f"\n{label} ({t.strftime('%H:%M')}):")
        print(f"  Period:           {top['time_period']}")
        print(f"  Base Hybrid Risk: {top['base_hybrid_risk']:.2f}")
        print(f"  Time Risk Factor: {top['time_risk']:.2f}")
        print(f"  Time-Aware Risk:  {top['route_risk']:.2f}")
        print(f"  Safety Score:     {top['safety_score']:.2f}")

    # Assertions
    morning_risk = results["Morning"][0]["route_risk"]
    afternoon_risk = results["Afternoon"][0]["route_risk"]
    evening_risk = results["Evening"][0]["route_risk"]
    late_night_risk = results["Late Night"][0]["route_risk"]

    print("\n" + "-" * 80)
    print(f"Risk Progression: Morning ({morning_risk:.2f}) < Afternoon ({afternoon_risk:.2f}) < Evening ({evening_risk:.2f}) < Late Night ({late_night_risk:.2f})")
    print("-" * 80)

    assert morning_risk < evening_risk, "Morning risk must be lower than evening risk"
    assert evening_risk < late_night_risk, "Evening risk must be lower than late night risk"
    assert results["Morning"][0]["safety_score"] > results["Late Night"][0]["safety_score"], "Morning safety must be higher than late night safety"
    print("\nSUCCESS: All time-aware risk assertions passed!\n")

if __name__ == "__main__":
    test_time_variation()

