import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.db.session import init_db

@pytest.mark.asyncio
async def test_full_saferoute_lifecycle():
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"
        print("\n[OK] Health check passed")

        # 2. User registration
        test_email = f"chennai_user_{int(asyncio.get_event_loop().time() * 1000)}@example.com"
        reg_res = await client.post("/api/auth/register", json={
            "email": test_email,
            "password": "secure_password_123",
            "name": "Priya Sharma",
        })
        assert reg_res.status_code == 201
        reg_data = reg_res.json()
        token = reg_data["access_token"]
        user_id = reg_data["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[OK] User registered: ID {user_id}")

        # 3. User login
        login_res = await client.post("/api/auth/login", json={
            "email": test_email,
            "password": "secure_password_123",
        })
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()
        print("[OK] User login successful")

        # 4. Check initial preferences & Twin state
        pref_res = await client.get("/api/users/me/preferences", headers=headers)
        assert pref_res.status_code == 200
        prefs = pref_res.json()
        assert prefs["lighting_preference"] == 0.7
        print("[OK] Initial preferences retrieved")

        twin_res = await client.get("/api/users/me/twin", headers=headers)
        assert twin_res.status_code == 200
        initial_twin = twin_res.json()
        print(f"[OK] Initial Twin state: confidence={initial_twin['model_confidence']}")

        # 5. Update preferences (high lighting and night safety sensitivity)
        update_pref_res = await client.put("/api/users/me/preferences", headers=headers, json={
            "lighting_preference": 0.95,
            "night_safety_weight": 0.90,
            "isolation_aversion": 0.85,
        })
        assert update_pref_res.status_code == 200
        assert update_pref_res.json()["lighting_preference"] == 0.95
        print("[OK] Preferences updated successfully")

        # 6. Trip Creation with Candidate Interactions
        trip_res = await client.post("/api/trips", headers=headers, json={
            "travel_date": "2026-09-23",
            "travel_time": "20:30",
            "source_zone": "Chennai Central",
            "destination_zone": "Marina Beach",
            "source_lat": 13.0827,
            "source_lon": 80.2707,
            "dest_lat": 13.0500,
            "dest_lon": 80.2824,
            "selected_route_id": 1,
            "selected_distance_km": 4.8,
            "selected_safety_score": 68.5,
            "interactions": [
                {
                    "route_id": 1,
                    "route_rank": 1,
                    "route_distance_km": 4.8,
                    "route_risk": 31.5,
                    "route_safety_score": 68.5,
                    "selected": True,
                },
                {
                    "route_id": 2,
                    "route_rank": 2,
                    "route_distance_km": 4.2,
                    "route_risk": 38.0,
                    "route_safety_score": 62.0,
                    "rejected": True,
                    "rejection_reason": "poor lighting",
                }
            ]
        })
        assert trip_res.status_code == 201
        trip = trip_res.json()
        trip_id = trip["id"]
        print(f"[OK] Trip created: {trip_id}")

        # 7. Live GPS Navigation Progress Simulation
        # Simulated route geometry (3 points)
        sample_geometry = [
            [80.2707, 13.0827],
            [80.2750, 13.0700],
            [80.2824, 13.0500],
        ]
        sample_instructions = [
            {"step": 1, "instruction": "Head south on Poonamallee High Rd", "distance_m": 1200},
            {"step": 2, "instruction": "Turn slight left onto Kamarajar Salai", "distance_m": 2500},
            {"step": 3, "instruction": "Arrive at Marina Beach", "distance_m": 0},
        ]

        start_nav = await client.post("/api/navigation/start", json={
            "trip_id": trip_id,
            "selected_route_index": 1,
            "geometry": sample_geometry,
            "instructions": sample_instructions,
            "destination_lat": 13.0500,
            "dest_lon": 80.2824,
        })
        assert start_nav.status_code == 200
        print("[OK] Navigation session started")

        # Ping 1: At starting position
        nav_update_1 = await client.post("/api/navigation/update", headers=headers, json={
            "trip_id": trip_id,
            "latitude": 13.0825,
            "longitude": 80.2708,
            "speed": 28.0,
        })
        assert nav_update_1.status_code == 200
        nav_status = nav_update_1.json()
        assert nav_status["off_route"] is False
        assert nav_status["step_number"] == 1
        print(f"[OK] Navigation ping 1: {nav_status['current_instruction']} | Next turn in {nav_status['distance_to_turn_formatted']}")

        # 8. Submit Trip Feedback & Trigger Personal Twin Learning
        feedback_res = await client.post(f"/api/trips/{trip_id}/feedback", headers=headers, json={
            "safety_rating": 2,
            "felt_unsafe": True,
            "lighting_rating": 2,
            "feedback_text": "Road was very dark near bridge, felt unsafe at night",
        })
        assert feedback_res.status_code == 200
        print("[OK] Trip feedback submitted with safety concern")

        # 9. Verify Twin Learning happened!
        twin_after_res = await client.get("/api/users/me/twin", headers=headers)
        assert twin_after_res.status_code == 200
        twin_after = twin_after_res.json()
        print(f"[OK] Updated Twin state: confidence={twin_after['model_confidence']} (was {initial_twin['model_confidence']})")
        print(f"     Lighting weight learned: {twin_after['lighting_weight']} (was {initial_twin['lighting_weight']})")
        print(f"     Crime weight learned:    {twin_after['crime_weight']} (was {initial_twin['crime_weight']})")
        
        # Verify learning increments
        assert twin_after["model_confidence"] > initial_twin["model_confidence"], "Twin confidence should increase"
        assert twin_after["lighting_weight"] > initial_twin["lighting_weight"], "Lighting sensitivity should increase after dark road feedback"
        assert twin_after["crime_weight"] > initial_twin["crime_weight"], "Crime weight should increase after feeling unsafe"
        print("[SUCCESS] All end-to-end backend tests passed!\n")

if __name__ == "__main__":
    asyncio.run(test_full_saferoute_lifecycle())

