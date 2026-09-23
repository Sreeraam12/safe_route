# SafeRoute — Existing Architecture & Final Implementation Roadmap

> **Project scope:** AI-powered women’s safe-route prediction and personalization system for **Chennai city**.
>
> This document records what is already implemented, what is currently incomplete, what must change in the Colab notebook, and the proposed final architecture including time-aware risk, Personal Digital Twin, database, authentication, dashboard, history, frontend, backend, testing, and deployment.

---

# 1. Executive Summary

SafeRoute currently has a working foundation for:

- Chennai road-network extraction using OpenStreetMap/OSMnx.
- Place-name geocoding.
- Nearest OSM-node matching.
- Candidate route generation.
- Crime-based risk.
- Environment-based fuzzy risk.
- Infrastructure-based fuzzy risk.
- A LightGBM road-risk model.
- Real historical weather integration using Open-Meteo.
- Hybrid road risk.
- Live traffic integration using TomTom.
- Route scoring and top-route selection.
- OSM route geometry.
- Turn-by-turn navigation instructions.
- FastAPI backend.
- Next.js + Leaflet frontend.
- Git/GitHub checkpointing.

The **current major missing functionality is time-aware route risk at request time**.

The current model already contains time features:

```text
hour
day_of_week
is_weekend
is_night
hour_sin
hour_cos
```

However, the project has not yet completed the full **request-time time-context pipeline** and has not implemented the intended **dynamic/fuzzy time-risk layer**.

The next major feature after time-aware risk is the **Personal Digital Twin**.

The final system should evolve from:

```text
Road → Risk
```

to:

```text
Road + Time + Weather + Traffic + User + User Behavior
                    ↓
          Personalized Route Risk
```

---

# 2. Current Project Architecture

## 2.1 Current high-level pipeline

```text
USER
  ↓
Source + Destination
  ↓
Geocoder
  ↓
Latitude / Longitude
  ↓
Nearest OSM Nodes
  ↓
Chennai OSM Driving Graph
  ↓
Candidate Route Generation
  ↓
Crime Risk
Environment Risk
Infrastructure Risk
Weather
Traffic
Time Features
  ↓
LightGBM
  ↓
ML Risk
  ↓
Hybrid Risk
  ↓
Live Traffic Adjustment
  ↓
Route Risk
  ↓
Route Safety Score
  ↓
Top Routes
  ↓
Map + Navigation
```

The current route engine is fundamentally **road-risk based**.

Personalization is not yet part of this pipeline.

---

# 3. What We Already Have

## 3.1 Dataset foundation

The development dataset package contains:

```text
01_chennai_safety_statistics.csv
02_crime_incidents.csv
03_road_segments.csv
04_road_environment.csv
05_safety_pois.csv
06_weather_data.csv
07_traffic_data.csv
08_segment_context_training.csv
09_fuzzy_rules.csv
10_data_lineage.csv
11_route_integration_schema.md
12_training_split_summary.csv
README.md
```

Important:

- Development crime/traffic/POI data are synthetic.
- Synthetic labels such as `target_risk_score` / `safety_score` are proxy labels.
- They must not be presented as actual Chennai safety probabilities.
- Production/final research validation should replace synthetic sources with verified data where possible.
- Exact personal information should not be included in the development dataset.

---

# 4. Existing ML Model

## 4.1 Current feature groups

The current LightGBM model uses 35 features.

### Crime

```text
crime_count_7d
crime_count_30d
crime_count_90d
high_severity_count
medium_severity_count
low_severity_count
weighted_crime_score
```

### Environment

```text
lighting_score
road_condition_score
visibility_score
sidewalk_score
pedestrian_score
crowd_score
isolation_score
```

### Infrastructure

```text
police_distance_km
hospital_distance_km
metro_distance_km
bus_stop_distance_km
police_points_500m
cctv_count_500m
```

### Traffic

```text
traffic_speed_kmph
free_flow_speed_kmph
congestion_ratio
travel_time_min
```

### Weather

```text
temperature_c
rainfall_mm
humidity
wind_speed_kmh
cloud_cover
```

### Time

```text
hour
day_of_week
is_weekend
is_night
hour_sin
hour_cos
```

Total:

```text
35 features
```

---

# 5. Current LightGBM Performance

The real-weather LightGBM model currently achieved approximately:

```text
Train:
MAE  = 3.5051
RMSE = 4.3982
R²   = 0.8656

Validation:
MAE  = 3.6542
RMSE = 4.5773
R²   = 0.8627

Test:
MAE  = 3.6915
RMSE = 4.6230
R²   = 0.8596
```

These results describe the current development model and should not be interpreted as real-world safety accuracy.

---

# 6. Current Time Implementation — Important Status

## What already exists

The model already receives time-related features.

The notebook defines:

```python
time_features = [
    "hour",
    "day_of_week",
    "is_weekend",
    "is_night",
    "hour_sin",
    "hour_cos",
]
```

The notebook also creates these features during OSM inference.

## What is NOT finished

The following is still incomplete:

```text
Requested travel date/time
        ↓
Request-time time context
        ↓
Dynamic time risk
        ↓
Time-aware hybrid risk
        ↓
Final route ranking
```

The clean continuation notebook explicitly identifies its next dynamic stage as:

1. Live/request-time traffic
2. Live/request-time weather
3. Departure-time context
4. Dynamic fuzzy risk
5. LightGBM inference at request time
6. Hybrid contextual risk
7. Top-5 route ranking
8. Turn-by-turn output
9. Google Routes/Maps integration
10. Quantum-inspired work later

Therefore, the clean notebook itself confirms that **departure-time context and dynamic fuzzy risk are the next missing stage**.

---

# 7. Important Notebook Issues to Fix

The uploaded clean continuation notebook contains several time-related implementations that must be made consistent.

## 7.1 Different `is_night` definitions exist

Some earlier notebook cells use:

```python
hour < 6 or hour >= 19
```

while a later inference cell uses:

```python
hour < 6 or hour >= 18
```

This must be standardized.

Recommended project definition:

```python
is_night = int(hour < 6 or hour >= 18)
```

Use the same definition everywhere:

- dataset generation
- training
- validation
- OSM inference
- backend
- Personal Twin context
- tests

Do not allow different thresholds in different layers.

---

# 8. Current Notebook Inference Problem

The notebook currently contains:

```python
INFERENCE_TIMESTAMP = pd.Timestamp("2026-08-27 18:00:00")
```

This is only a fixed test timestamp.

It must eventually become:

```text
User travel_date
+
User travel_time
        ↓
travel_datetime
        ↓
time features
        ↓
weather selection
        ↓
traffic selection
        ↓
ML inference
```

The backend already accepts:

```text
travel_date
travel_time
```

so the notebook work should prepare the inference architecture that the backend will later reproduce.

---

# 9. Weather Status

## Already implemented

Historical Chennai weather has been obtained using Open-Meteo.

Current weather dataset:

```text
2026-03-01 → 2026-08-27
```

The training weather values were aligned with timestamps.

The model currently uses:

```text
temperature_c
rainfall_mm
humidity
wind_speed_kmh
cloud_cover
```

## Required next behavior

### Historical requested trip

Use historical weather:

```text
travel_datetime
      ↓
historical weather API/data
```

### Current trip

Use current/live weather:

```text
current time
      ↓
current weather API
```

### Near-future trip

Use forecast weather:

```text
future travel_datetime
      ↓
weather forecast
```

### Far-future trip

Use a clearly defined fallback/baseline.

Do not pretend exact future weather is known.

---

# 10. Traffic Status

Current project has TomTom live traffic integration.

It can provide:

```text
current speed
free-flow speed
travel time
congestion ratio
road closure
traffic risk
```

The project currently samples route points and matches live traffic observations to OSM segments.

## Important limitation

TomTom live traffic is **not historical training traffic**.

The existing training traffic data are synthetic/development data.

Therefore:

```text
Training traffic distribution
        ≠
Live TomTom traffic distribution
```

This creates potential feature-distribution mismatch.

For the research/final version:

- Use legitimate historical traffic if available.
- Or explicitly treat live traffic as a runtime adjustment rather than claiming it trained the model.
- Keep the distinction documented.

---

# 11. Current Hybrid Risk

The notebook currently computes:

```python
hybrid_risk_100 = (
    0.70 * ml_risk_100
    + 0.10 * crime_risk_100
    + 0.10 * environment_risk_100
    + 0.10 * infrastructure_risk_100
)
```

then:

```python
safety_score = 100 - hybrid_risk_100
```

This is the current static/contextual foundation.

The next stage should extend this rather than destroy the existing model.

---

# 12. Current Traffic Route Combination

The notebook currently combines existing route risk with live traffic approximately as:

```text
90% existing route risk
10% traffic risk
```

The backend was designed around the same concept.

This should remain a separate traffic layer unless we later retrain the global model using proper historical traffic.

---

# 13. Current Backend

Project root:

```text
C:\vs_code_projects\safe_route
```

Backend:

```text
backend/
├── artifacts/
└── app/
    ├── api/
    ├── schemas/
    ├── services/
    └── main.py
```

## Current services

```text
geocoder.py
route_engine.py
ml_engine.py
risk_engine.py
candidate_route_engine.py
route_scoring.py
traffic_engine.py
final_route_engine.py
route_geometry.py
```

## Current backend capabilities

### Geocoding

Place name → latitude/longitude.

### OSM routing

Coordinates → nearest OSM node → shortest route.

### Candidate routes

Generates multiple alternatives using edge penalties and overlap/distance constraints.

### ML inference

Loads:

```text
saferoute_lightgbm_real_weather.txt
saferoute_ml_features_35.json
```

### Risk engine

Uses cached OSM risk artifacts.

### Traffic engine

Uses live TomTom traffic.

### Geometry

Provides actual OSM geometry and turn-by-turn instructions.

### Final route engine

Intended final pipeline:

```text
Candidate routes
      ↓
Hybrid risk
      ↓
Traffic risk
      ↓
Final risk
      ↓
Final safety
      ↓
Top 5
```

---

# 14. Current API

Current API includes:

```text
GET /health

POST /api/routes/geocode

POST /api/routes/search
```

The route search request contains:

```json
{
  "source": "...",
  "destination": "...",
  "travel_date": "YYYY-MM-DD",
  "travel_time": "HH:MM",
  "travel_mode": "driving"
}
```

The backend combines date + time into a travel datetime.

This is important because the frontend/backend contract is already prepared for time-aware routing.

---

# 15. Current Frontend

Technology:

```text
Next.js
TypeScript
Leaflet
```

Current components:

```text
SearchPanel
SafeRouteMap
RouteList
RouteDetails
routeApi
route types
```

Current functionality:

- Source search.
- Destination search.
- Travel date.
- Travel time.
- Travel mode.
- Route search.
- Multiple route display.
- Selected route highlighting.
- Route details.
- Route results closing.
- Map markers.
- Route geometry.
- Top route information.
- Turn-by-turn information.

---

# 16. Current Git Status

The project is already pushed to GitHub.

This is important because the development strategy can now be:

```text
Existing Git commit
        ↓
Create feature branch
        ↓
Implement time-aware risk
        ↓
Test
        ↓
Commit
        ↓
Implement Personal Twin
        ↓
Test
        ↓
Commit
```

Do not directly destroy the working version.

Recommended branches:

```text
main
develop
feature/time-risk
feature/personal-twin
feature/database
feature/auth
feature/dashboard
feature/history
```

---

# 17. Phase 1 — Finish Time-Aware Risk

This is the immediate next milestone.

## Goal

The same route request should produce different risk values when the requested departure time changes.

Example:

```text
Chennai Central → Marina Beach

10:00 AM
      ↓
risk A

02:00 PM
      ↓
risk B

07:00 PM
      ↓
risk C

11:00 PM
      ↓
risk D
```

The system must not merely accept the time field.

The time must influence the actual risk/ranking pipeline.

---

# 18. Time-Aware Risk Architecture

The proposed architecture:

```text
Travel Date + Time
        ↓
Time Context Builder
        ↓
 ┌─────────────────────────────┐
 │ hour                        │
 │ day_of_week                 │
 │ weekend                     │
 │ night                       │
 │ hour_sin                    │
 │ hour_cos                    │
 └─────────────────────────────┘
        ↓
Global LightGBM
        ↓
ML Risk
        +
Dynamic Time Risk
        ↓
Contextual Risk
        ↓
Crime + Environment + Infrastructure
        ↓
Hybrid Risk
        ↓
Traffic Adjustment
        ↓
Final Route Risk
```

---

# 19. Should We Train a Separate Time Model?

Not necessarily.

The current LightGBM already has time features.

A better staged design is:

```text
Existing LightGBM
        +
Explicit dynamic/fuzzy time layer
```

This avoids unnecessarily creating a second model only for `hour`.

The explicit time layer can model domain logic such as:

- daylight
- evening transition
- night
- late night
- weekend
- time-dependent safety context

The exact weights/rules should be validated experimentally rather than arbitrarily claiming that a particular time is objectively unsafe.

---

# 20. Time-Risk Implementation in Colab

The clean notebook should be extended after the existing static-risk stage.

## Required notebook work

### A. Validate time features

Check:

```text
hour
day_of_week
is_weekend
is_night
hour_sin
hour_cos
```

for training and inference.

### B. Standardize `is_night`

Use one definition everywhere.

### C. Verify time effect

For identical road/environment/crime/infrastructure conditions, generate predictions for:

```text
06:00
09:00
12:00
15:00
18:00
21:00
00:00
```

Compare:

```text
ML risk
ML safety
time risk
final contextual risk
```

### D. Implement dynamic fuzzy time risk

Build membership functions/rules for the time context.

Example conceptual variables:

```text
hour:
  morning
  afternoon
  evening
  night
  late_night

day:
  weekday
  weekend
```

Output:

```text
time_risk_100
```

### E. Combine

Potential structure:

```text
ML risk
+
time contextual risk
+
existing crime/environment/infrastructure
```

The exact combination should be tested and documented.

### F. Request-time inference

Replace:

```python
INFERENCE_TIMESTAMP = ...
```

with a function that receives:

```python
travel_datetime
```

### G. Save the resulting artifacts

Example:

```text
saferoute_lightgbm_real_weather.txt
saferoute_ml_features_35.json
time_risk_rules.json
time_risk_parameters.json
```

---

# 21. Time-Risk Testing Requirements

Before moving to Personal Twin, test:

## Test 1 — Same route, different time

```text
Source: Chennai Central
Destination: Marina Beach

08:00
14:00
18:00
22:00
```

Expected:

```text
risk values should be generated independently
```

Do not require every route to change dramatically. The important requirement is that time context is actually incorporated.

## Test 2 — Same date, different time

Check that only time-related context changes.

## Test 3 — Weekday vs weekend

Compare:

```text
Monday 20:00
Saturday 20:00
```

## Test 4 — Backend

Send two API requests with different times.

Verify that:

```text
route risk
safety score
ranking
```

are calculated from the requested time.

## Test 5 — Frontend

Change travel time and submit again.

Verify the displayed results update.

---

# 22. Phase 2 — Database Foundation

Once time-aware routing works, build the user/personalization backend.

Recommended database:

```text
PostgreSQL
```

Do not store the Personal Twin only in frontend state.

The database must persist the user’s learned state.

---

# 23. Proposed Database Schema

## `users`

```text
id
email
password_hash
name
created_at
updated_at
```

Avoid storing unnecessary sensitive information.

---

## `personal_preferences`

```text
user_id
lighting_preference
crowd_preference
isolation_aversion
cctv_preference
police_proximity_preference
main_road_preference
crime_sensitivity
traffic_tolerance
distance_priority
time_priority
detour_tolerance
night_safety_weight
weather_sensitivity
updated_at
```

These are the user's initial preferences.

They are not necessarily the final learned preferences.

---

## `trips`

```text
id
user_id
trip_datetime
travel_date
travel_time
source_zone
destination_zone
travel_mode
trip_intent
selected_route_id
selected_distance_km
selected_duration_min
selected_safety_score
actual_distance_km
actual_duration_min
route_deviation_pct
weather_condition
traffic_condition
completed
created_at
```

Prefer zones/geohashes rather than exact home addresses where possible.

---

## `route_interactions`

One row per candidate route shown for a trip.

```text
id
trip_id
user_id
route_id
route_rank
route_distance_km
route_duration_min
route_risk
route_safety_score
lighting_score
crowd_score
isolation_score
crime_risk
traffic_risk
viewed
selected
rejected
rejection_reason
```

This is one of the most important datasets for learning the user's behavior.

---

## `trip_feedback`

```text
id
trip_id
user_id
safety_rating
comfort_rating
lighting_rating
crowd_rating
navigation_rating
incident_reported
incident_type
felt_unsafe
feedback_text
created_at
```

Feedback should be optional.

---

## `personal_segment_memory`

```text
id
user_id
osm_segment_id
visit_count
selection_count
rejection_count
positive_feedback_count
negative_feedback_count
avoidance_score
trust_score
personal_risk_adjustment
last_visit
confidence
```

This gives the Personal Twin road-level memory.

---

## `personal_twin_state`

This stores the current learned state.

```text
user_id
timestamp
lighting_weight
crime_weight
isolation_weight
crowd_weight
traffic_weight
distance_weight
time_weight
night_weight
weather_weight
detour_tolerance
model_confidence
```

This is the current state of the user's Digital Twin.

Raw history remains immutable.

---

# 24. Personal Digital Twin Concept

The Personal Twin is not simply:

```text
User profile
```

It is:

```text
User profile
+
Preferences
+
Observed choices
+
Route history
+
Feedback
+
Segment memory
+
Context
```

It continuously represents the user's current routing preferences.

---

# 25. Personal Twin Data Flow

```text
USER
  ↓
Login
  ↓
Personal Twin
  ↓
Current Twin State
  ↓
Route Search
  ↓
Existing SafeRoute
  ↓
Global Road Risk
  ↓
Personal Risk Adjustment
  ↓
Personalized Route Risk
  ↓
Top 5 Routes
  ↓
User Views Routes
  ↓
User Selects Route
  ↓
Trip Completed
  ↓
Feedback / Behavioral Evidence
  ↓
Learning Engine
  ↓
Updated Twin State
  ↓
Next Trip
```

This is the central new architecture.

---

# 26. Personal Twin Dataset

For development/testing, create:

```text
personal_twin_dataset/
├── 01_personal_users.csv
├── 02_personal_preferences.csv
├── 03_personal_trips.csv
├── 04_route_interactions.csv
├── 05_personal_feedback.csv
├── 06_personal_segment_memory.csv
├── 07_personal_twin_state.csv
└── README.md
```

---

# 27. Personal Users Dataset

Fields:

```text
user_id
age_group
gender
occupation_type
default_travel_mode
mobility_category
```

Use coarse categories.

Do NOT collect:

```text
Aadhaar
password
contacts
private messages
exact home address
unnecessary sensitive information
```

Synthetic users must be labelled as synthetic.

---

# 28. Personal Preferences Dataset

Fields:

```text
user_id
lighting_preference
crowd_preference
isolation_aversion
cctv_preference
police_proximity_preference
main_road_preference
crime_sensitivity
traffic_tolerance
distance_priority
time_priority
detour_tolerance
night_safety_weight
weather_sensitivity
```

Initial preference values should normally be normalized:

```text
0.0 → 1.0
```

---

# 29. Personal Trip Dataset

Fields:

```text
trip_id
user_id
trip_datetime
travel_date
travel_time
source_zone
destination_zone
travel_mode
trip_intent
selected_route_id
selected_distance_km
selected_duration_min
selected_safety_score
actual_distance_km
actual_duration_min
route_deviation_pct
weather_condition
traffic_condition
completed
```

---

# 30. Route Interaction Dataset

This captures what the user actually preferred.

For every candidate route:

```text
trip
 ↓
Route 1
Route 2
Route 3
Route 4
Route 5
```

Record:

```text
viewed
selected
rejected
rejection_reason
```

along with route properties.

This creates behavioral training evidence.

---

# 31. Personal Feedback Dataset

After a completed trip, optionally ask:

```text
How safe did you feel?
How comfortable was the route?
How was the lighting?
How was the crowd level?
How was navigation?
Did you encounter anything concerning?
```

Keep it short so users actually provide feedback.

---

# 32. Personal Segment Memory

The system learns road-specific behavior.

Example:

```text
OSM Segment 123

User A:
visit_count = 10
selection_count = 8
positive_feedback = 7
trust_score = high

User B:
visit_count = 8
rejection_count = 6
negative_feedback = 5
avoidance_score = high
```

The same road can therefore receive different personalized adjustments.

This is one of the key differentiating concepts of SafeRoute.

---

# 33. Personal Twin Learning

Do NOT blindly change preferences after every trip.

Instead:

```text
New trip evidence
      ↓
Existing twin state
      ↓
Weighted update
      ↓
Confidence calculation
      ↓
Updated twin state
```

Example:

If a user repeatedly chooses:

```text
longer
but safer
routes
```

then gradually:

```text
safety_weight ↑
distance_weight ↓
detour_tolerance ↑
```

If a user repeatedly chooses well-lit routes at night:

```text
night_weight ↑
lighting_weight ↑
```

The change should be gradual.

---

# 34. Global Model vs Personal Twin

This separation is critical.

## Global LightGBM

Learns:

```text
General road-risk patterns
```

Update:

```text
periodically
```

NOT:

```text
after every user trip
```

## Personal Twin

Learns:

```text
User-specific behavior
```

Update:

```text
after trips / feedback
```

Architecture:

```text
GLOBAL MODEL
    ↓
Base road risk

PERSONAL TWIN
    ↓
Personal adjustment

Together
    ↓
Personalized risk
```

---

# 35. Personal Risk Formula

Conceptually:

```text
base_road_risk
        +
personal_adjustment
        ↓
personalized_risk
```

A more detailed version can use:

```text
Personalized Risk =
Base Risk
+ Lighting Adjustment
+ Crime Sensitivity Adjustment
+ Isolation Adjustment
+ Crowd Adjustment
+ Traffic Adjustment
+ Night Adjustment
+ Weather Adjustment
```

Then clip to:

```text
0–100
```

The exact weights should be configurable and experimentally validated.

---

# 36. Contextual Personalization

The twin should not apply the same adjustment in every situation.

Example:

```text
User has high night-safety preference
```

At:

```text
2 PM
```

night preference should have little/no effect.

At:

```text
10 PM
```

night preference should have much stronger influence.

Therefore:

```text
Personal Twin
      +
Current Context
      ↓
Contextual Personal Adjustment
```

This is more meaningful than a static profile.

---

# 37. Backend Changes for Personal Twin

Add:

```text
services/
├── personal_twin_engine.py
├── personalization_engine.py
└── twin_learning_engine.py
```

Potential models:

```text
models/
├── user.py
├── trip.py
├── preferences.py
└── twin.py
```

Potential APIs:

```text
POST /api/auth/register
POST /api/auth/login

GET  /api/users/me
GET  /api/users/me/preferences
PUT  /api/users/me/preferences

POST /api/routes/search

POST /api/trips
GET  /api/trips
GET  /api/trips/{trip_id}

POST /api/trips/{trip_id}/feedback

GET /api/twin
```

Exact endpoint naming can be finalized during implementation.

---

# 38. Authentication

Required for Personal Twin.

Recommended:

```text
Email
Password
JWT/session authentication
```

Flow:

```text
Register
 ↓
Login
 ↓
Authentication token/session
 ↓
User ID
 ↓
Load Personal Twin
```

Never store plain-text passwords.

Use proper password hashing.

---

# 39. Frontend — Login

Add:

```text
/login
/register
```

Registration:

```text
Name
Email
Password
Confirm Password
```

After login:

```text
Dashboard
```

---

# 40. Frontend — Dashboard

Dashboard should show:

```text
Welcome
Recent trips
Saved/frequent routes
Personal safety preferences
Current twin summary
Trip statistics
```

Possible statistics:

```text
Trips completed
Average route distance
Average selected safety score
Average travel time
Routes preferred
Night trips
```

Avoid exposing raw sensitive information unnecessarily.

---

# 41. Frontend — Preferences

Create a preferences screen.

Possible controls:

```text
Lighting importance
Crowd preference
Isolation avoidance
CCTV preference
Police proximity
Crime sensitivity
Traffic tolerance
Distance priority
Time priority
Night safety
Weather sensitivity
Detour tolerance
```

The user can initialize their Personal Twin here.

---

# 42. Frontend — Route Search Enhancement

Current search:

```text
From
To
Date
Time
Travel Mode
```

Keep this.

Add later:

```text
Trip intent
```

Possible examples:

```text
Work
College
Shopping
Emergency
Personal
Other
```

Trip intent should only be collected if it provides a demonstrated modeling benefit.

---

# 43. Frontend — Route Results Enhancement

Each route card should eventually show:

```text
Route Rank
Safety Score
Risk Level
Distance
Estimated Time
Traffic
Crime Risk
Lighting
Crowd
Personalized Adjustment
```

Potential explanation:

```text
Why this route?
```

Example:

```text
Higher lighting
Lower isolation
Lower traffic
Preferred based on your past route choices
```

This improves explainability.

---

# 44. Frontend — Trip Completion

After route selection:

```text
Start Trip
```

After trip:

```text
Complete Trip
```

Then optional:

```text
Safety rating
Comfort rating
Lighting rating
Crowd rating
Navigation rating
Felt unsafe?
Incident report
```

This becomes learning data.

---

# 45. Frontend — History

Add:

```text
/history
```

Show:

```text
Date
Source
Destination
Selected route
Distance
Duration
Safety score
Completed
```

Clicking a trip:

```text
Trip details
Route map
Risk breakdown
Feedback
```

---

# 46. Frontend — Dashboard Architecture

Final frontend structure:

```text
src/
├── app/
│   ├── login/
│   ├── register/
│   ├── dashboard/
│   ├── routes/
│   ├── history/
│   ├── preferences/
│   └── profile/
│
├── components/
│   ├── auth/
│   ├── dashboard/
│   ├── map/
│   ├── routes/
│   ├── search/
│   ├── history/
│   ├── preferences/
│   └── feedback/
│
├── services/
│   ├── authApi.ts
│   ├── routeApi.ts
│   ├── tripApi.ts
│   ├── preferenceApi.ts
│   └── twinApi.ts
│
└── types/
    ├── auth.ts
    ├── route.ts
    ├── trip.ts
    └── twin.ts
```

---

# 47. Final Backend Architecture

Proposed:

```text
backend/
├── artifacts/
│
└── app/
    ├── api/
    │   ├── auth.py
    │   ├── routes.py
    │   ├── users.py
    │   ├── trips.py
    │   └── twin.py
    │
    ├── schemas/
    │   ├── auth.py
    │   ├── route.py
    │   ├── trip.py
    │   └── twin.py
    │
    ├── models/
    │   ├── user.py
    │   ├── trip.py
    │   ├── preferences.py
    │   └── twin.py
    │
    ├── services/
    │   ├── geocoder.py
    │   ├── route_engine.py
    │   ├── candidate_route_engine.py
    │   ├── ml_engine.py
    │   ├── risk_engine.py
    │   ├── traffic_engine.py
    │   ├── time_risk_engine.py
    │   ├── final_route_engine.py
    │   ├── route_geometry.py
    │   ├── personal_twin_engine.py
    │   ├── personalization_engine.py
    │   └── twin_learning_engine.py
    │
    └── main.py
```

---

# 48. Final Database Architecture

```text
PostgreSQL
    │
    ├── users
    ├── personal_preferences
    ├── trips
    ├── route_interactions
    ├── trip_feedback
    ├── personal_segment_memory
    └── personal_twin_state
```

The database becomes the persistent memory of SafeRoute.

---

# 49. Final End-to-End Architecture

```text
                         ┌─────────────────────┐
                         │       USER          │
                         └──────────┬──────────┘
                                    │
                         Login / Preferences
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   PERSONAL TWIN     │
                         │                     │
                         │ Preferences         │
                         │ History             │
                         │ Behavior            │
                         │ Feedback            │
                         │ Segment Memory      │
                         │ Twin State          │
                         └──────────┬──────────┘
                                    │
                                    ▼
Source + Destination + Date + Time + Mode + Intent
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      GEOCODER       │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │     CHENNAI OSM     │
                         │    ROAD NETWORK     │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ CANDIDATE ROUTES    │
                         └──────────┬──────────┘
                                    │
                  ┌─────────────────┼──────────────────┐
                  ▼                 ▼                  ▼
              Crime          Environment        Infrastructure
                  │                 │                  │
                  └─────────────────┼──────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     TIME CONTEXT    │
                         │ hour/day/night/etc. │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   WEATHER CONTEXT   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   TRAFFIC CONTEXT   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   GLOBAL LIGHTGBM   │
                         └──────────┬──────────┘
                                    ▼
                              Base ML Risk
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   HYBRID RISK       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ PERSONAL ADJUSTMENT │
                         │    + TWIN STATE     │
                         └──────────┬──────────┘
                                    ▼
                         Personalized Route Risk
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    ROUTE RANKING    │
                         └──────────┬──────────┘
                                    ▼
                              TOP 5 ROUTES
                                    │
                  ┌─────────────────┼──────────────────┐
                  ▼                 ▼                  ▼
                Map           Instructions       Risk Breakdown
                                    │
                                    ▼
                              USER SELECTS
                                    │
                                    ▼
                              TRIP EXECUTION
                                    │
                                    ▼
                         Trip + Interaction Data
                                    │
                                    ▼
                           Optional Feedback
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ TWIN LEARNING      │
                         │      ENGINE         │
                         └──────────┬──────────┘
                                    ▼
                           Updated Twin State
                                    │
                                    └───────────────► NEXT TRIP
```

---

# 50. Data Flow for the Personal Twin

The complete learning loop:

```text
Initial user
    ↓
Initial preferences
    ↓
Initial twin state
    ↓
Trip request
    ↓
Personalized routes
    ↓
Route choices
    ↓
Actual trip
    ↓
Feedback
    ↓
Behavior evidence
    ↓
Twin update
    ↓
New twin state
    ↓
Next trip
```

This is the core "digital twin" behavior.

---

# 51. What the Personal Twin Does NOT Do

It should NOT:

```text
retrain LightGBM after every trip
```

It should NOT:

```text
overwrite the entire user profile after one trip
```

It should NOT:

```text
store unnecessary personal/private information
```

It should NOT:

```text
claim that a user's preference is certain after one observation
```

Instead:

```text
historical evidence
+
confidence
+
gradual update
```

---

# 52. Personal Twin Confidence

Every learned preference should ideally have a confidence component.

Example:

```text
lighting_weight = 0.82
confidence = 0.71
```

After more observations:

```text
lighting_weight = 0.86
confidence = 0.89
```

This allows the system to distinguish:

```text
strong learned preference
```

from:

```text
weak early evidence
```

---

# 53. Explainability

The final system should explain route recommendations.

Instead of only:

```text
Safety Score: 82
```

show:

```text
Safety Score: 82

Why:
✓ Better lighting
✓ Lower crime exposure
✓ Lower isolation
✓ Lower traffic
✓ Matches your preference for well-lit roads
```

This is especially important because the Personal Twin changes the ranking.

---

# 54. Security & Privacy

Required:

- Password hashing.
- Authenticated APIs.
- User-level database authorization.
- Never expose another user's trips.
- Never expose Personal Twin state of another user.
- Avoid exact home-address storage where possible.
- Use zones/geohashes where practical.
- Keep raw history separate from current twin state.
- Keep API keys in `.env`.
- Do not commit secrets to GitHub.
- Add proper CORS configuration.
- Validate all request inputs.

---

# 55. Testing Strategy

## Backend unit tests

Test:

```text
geocoder
time feature generation
time risk
ML feature construction
risk calculation
candidate routes
route scoring
traffic matching
personalization
twin learning
```

## API tests

Test:

```text
register
login
preferences
route search
trip creation
trip history
feedback
twin retrieval
```

## Integration tests

Test:

```text
login
 ↓
route search
 ↓
route selection
 ↓
trip creation
 ↓
feedback
 ↓
twin update
 ↓
next route search
```

## Personalization test

Important test:

```text
Trip 1:
User prefers well-lit route

       ↓

Twin updated

       ↓

Trip 2:
Same source/destination/context

       ↓

Route scoring reflects updated preference
```

This is one of the most important demonstrations for the project.

---

# 56. Research Experiments

The final project should compare:

### Experiment A

```text
Static SafeRoute
```

vs

### Experiment B

```text
Time-aware SafeRoute
```

vs

### Experiment C

```text
Time + Personal Twin SafeRoute
```

Compare:

```text
route risk
route changes
safety score
distance
travel time
user preference alignment
```

Do not claim the personalized version is universally better without empirical evaluation.

---

# 57. Ablation Study

Useful research experiment:

```text
Full model
        ↓
Remove time
        ↓
Remove crime
        ↓
Remove environment
        ↓
Remove infrastructure
        ↓
Remove traffic
        ↓
Remove Personal Twin
```

Measure how the outputs change.

This strengthens the research contribution.

---

# 58. Personal Twin Synthetic Development Data

Create several synthetic user archetypes.

### Safety First

```text
high lighting preference
high crime sensitivity
high isolation aversion
high detour tolerance
```

### Time Sensitive

```text
high time priority
low detour tolerance
higher traffic tolerance
```

### Balanced

```text
moderate weights
```

### Night Sensitive

```text
high night safety
high lighting
high crowd preference
```

### Weather Sensitive

```text
high weather sensitivity
```

All such data must be explicitly labelled:

```text
SYNTHETIC DEVELOPMENT DATA
```

---

# 59. Personal Twin Validation

Example:

```text
User A:
initial detour tolerance = 0.30

User repeatedly selects:
longer + safer routes

After multiple trips:
detour tolerance increases
```

Another:

```text
User B:
repeatedly rejects isolated roads

Twin:
isolation_aversion increases
```

Then run a new route search and verify that the ranking changes according to the learned state.

---

# 60. Database Connectivity Plan

Recommended stack:

```text
FastAPI
   ↓
SQLAlchemy / SQLModel
   ↓
PostgreSQL
```

Environment variables:

```text
DATABASE_URL=...
JWT_SECRET=...
TOMTOM_API_KEY=...
```

Do not hardcode credentials.

Development:

```text
Local PostgreSQL
```

Later:

```text
Hosted PostgreSQL
```

---

# 61. Migration Plan

Do not build everything at once.

Recommended order:

```text
1. Database setup
2. User model
3. Authentication
4. Preferences
5. Trip storage
6. Route interactions
7. Feedback
8. Twin state
9. Twin learning
10. Personalized route scoring
```

---

# 62. Recommended Implementation Order

## Milestone 1 — Time-aware routing

```text
Colab
 ↓
Time context
 ↓
Dynamic time risk
 ↓
Validation
 ↓
Artifacts
```

Then:

```text
Backend
 ↓
time_risk_engine.py
 ↓
request-time inference
 ↓
route ranking
```

Then:

```text
Frontend
 ↓
verify date/time changes
```

---

## Milestone 2 — PostgreSQL

```text
PostgreSQL
 ↓
SQLAlchemy/SQLModel
 ↓
models
 ↓
migrations
```

---

## Milestone 3 — Authentication

```text
Register
Login
JWT/session
Protected routes
```

---

## Milestone 4 — User Preferences

```text
Preference UI
 ↓
Database
 ↓
Initial Twin State
```

---

## Milestone 5 — Trip History

```text
Route search
 ↓
Selected route
 ↓
Trip record
 ↓
History page
```

---

## Milestone 6 — Route Interaction Logging

Record:

```text
viewed
selected
rejected
route attributes
```

---

## Milestone 7 — Feedback

After trip:

```text
feedback
 ↓
database
```

---

## Milestone 8 — Personal Twin Learning

```text
Trip history
+
Route interactions
+
Feedback
 ↓
Learning engine
 ↓
Twin state
```

---

## Milestone 9 — Personalized Routing

```text
Global risk
+
Twin state
+
Context
 ↓
Personalized risk
 ↓
Top 5
```

---

## Milestone 10 — Dashboard & Research Evaluation

Build:

```text
Dashboard
History
Preferences
Twin summary
Statistics
```

Then perform experiments and evaluation.

---

# 63. Final Project Structure

```text
safe_route/
│
├── backend/
│   ├── artifacts/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── routes.py
│   │   │   ├── users.py
│   │   │   ├── trips.py
│   │   │   └── twin.py
│   │   │
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── preferences.py
│   │   │   ├── trip.py
│   │   │   └── twin.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── route.py
│   │   │   ├── trip.py
│   │   │   └── twin.py
│   │   │
│   │   ├── services/
│   │   │   ├── geocoder.py
│   │   │   ├── route_engine.py
│   │   │   ├── candidate_route_engine.py
│   │   │   ├── ml_engine.py
│   │   │   ├── risk_engine.py
│   │   │   ├── time_risk_engine.py
│   │   │   ├── traffic_engine.py
│   │   │   ├── route_scoring.py
│   │   │   ├── final_route_engine.py
│   │   │   ├── route_geometry.py
│   │   │   ├── personal_twin_engine.py
│   │   │   ├── personalization_engine.py
│   │   │   └── twin_learning_engine.py
│   │   │
│   │   └── main.py
│   │
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   ├── dashboard/
│   │   │   ├── history/
│   │   │   ├── preferences/
│   │   │   └── profile/
│   │   │
│   │   ├── components/
│   │   ├── services/
│   │   └── types/
│   │
│   └── .env.local
│
├── personal_twin_dataset/
│   ├── 01_personal_users.csv
│   ├── 02_personal_preferences.csv
│   ├── 03_personal_trips.csv
│   ├── 04_route_interactions.csv
│   ├── 05_personal_feedback.csv
│   ├── 06_personal_segment_memory.csv
│   ├── 07_personal_twin_state.csv
│   └── README.md
│
├── tests/
│
├── README.md
└── .gitignore
```

---

# 64. Colab Notebook — Exact Role Going Forward

The uploaded clean continuation notebook should remain the **ML/data-engineering source of truth**.

Its current structure is:

```text
Static OSM/risk preparation
        ↓
Dynamic features + LightGBM
        ↓
Real weather
        ↓
LightGBM training
        ↓
OSM inference
        ↓
Hybrid risk
        ↓
TomTom traffic
        ↓
Route ranking
```

The important current cells are approximately:

```text
31   → feature definitions
30   → segment context training dataset
199  → final 35-feature definition
200  → weather column correction
201  → feature validation
203  → target/split validation
204  → train/validation/test matrices
205  → LightGBM training
206  → evaluation
213  → inference timestamp
214  → weather assignment
216  → OSM ML prediction
226/227 → hybrid risk
229  → model artifact saving
237+ → TomTom traffic integration
272+ → final route scoring/ranking
280+ → checkpoint saving
```

These are notebook execution positions, not a guarantee that the visible Colab execution count will remain identical after edits.

---

# 65. Colab Changes Required for Time Risk

Do NOT delete the current 35-feature LightGBM pipeline.

Instead:

```text
Keep:
35-feature model
```

Add:

```text
time context validation
dynamic time risk
request-time inference
time-risk artifact
```

The notebook should produce artifacts that the backend can consume.

Potential artifacts:

```text
saferoute_lightgbm_real_weather.txt
saferoute_ml_features_35.json
time_risk_rules.json
time_risk_config.json
```

---

# 66. Colab Changes Required for Personal Twin

The Personal Twin should NOT be trained inside the current road-risk notebook as one giant model.

Keep the responsibilities separate.

### Colab / ML notebook

Responsible for:

```text
global road risk
time risk
weather
traffic
crime
environment
infrastructure
```

### Backend / database

Responsible for:

```text
user history
preferences
route interactions
feedback
twin state
personal learning
```

Later, if research requires a learned personalization model, a separate notebook can be created:

```text
Personal_Twin_Training.ipynb
```

That notebook can analyze:

```text
route_interactions
trip_feedback
personal_segment_memory
```

and evaluate personalization algorithms.

---

# 67. Separate Personal Twin Research Notebook

Eventually create:

```text
Personal_Twin_Training.ipynb
```

Sections:

```text
1. Load synthetic/user data
2. Explore preferences
3. Analyze route choices
4. Generate behavioral features
5. Learn preference weights
6. Update confidence
7. Segment-level memory
8. Personalized risk calculation
9. Compare global vs personalized ranking
10. Evaluate personalization
```

Do this only after the database + behavioral data pipeline exists.

---

# 68. Quantum-Inspired Optimization

Keep this as a later research enhancement.

Current priority:

```text
Time-aware risk
        ↓
Personal Twin
        ↓
Evaluation
        ↓
Quantum-inspired route optimization
```

Do not block the main product architecture on the quantum component.

---

# 69. What We Should NOT Do Now

Do not immediately:

```text
❌ Rebuild the entire ML model
❌ Delete the existing OSM risk artifacts
❌ Retrain LightGBM after every trip
❌ Build the Personal Twin before time-risk works
❌ Put user history only in frontend/localStorage
❌ Mix global ML training with user personalization
❌ Claim TomTom live traffic is historical training data
❌ Treat synthetic safety labels as real Chennai probabilities
❌ Store unnecessary personal data
❌ Hardcode travel time in backend inference
```

---

# 70. Immediate Next Action

The development sequence should begin exactly here:

```text
CURRENT WORKING SYSTEM
        ↓
TIME-AWARE RISK
        ↓
Validate in Colab
        ↓
Export time-risk artifacts
        ↓
Integrate backend
        ↓
Test same route at different times
        ↓
Commit to Git
        ↓
POSTGRESQL
        ↓
AUTH
        ↓
USER PREFERENCES
        ↓
TRIP HISTORY
        ↓
ROUTE INTERACTIONS
        ↓
FEEDBACK
        ↓
PERSONAL TWIN STATE
        ↓
TWIN LEARNING
        ↓
PERSONALIZED ROUTING
        ↓
DASHBOARD
        ↓
FINAL EVALUATION
```

---

# 71. Final Definition of Done

SafeRoute is considered functionally complete when:

## Routing

- [ ] Chennai geocoding works.
- [ ] OSM routing works.
- [ ] Candidate routes are generated.
- [ ] Top 5 routes are returned.
- [ ] Geometry is correct.
- [ ] Navigation instructions are generated.

## Global risk

- [ ] Crime risk works.
- [ ] Environment risk works.
- [ ] Infrastructure risk works.
- [ ] LightGBM works.
- [ ] Weather works.
- [ ] Traffic works.
- [ ] Hybrid risk works.

## Time-aware risk

- [ ] Travel date is used.
- [ ] Travel time is used.
- [ ] Time features are generated consistently.
- [ ] Dynamic time risk exists.
- [ ] Same route can be evaluated at different times.
- [ ] Time affects final route scoring.
- [ ] Time-aware inference is used by backend.

## Personal Twin

- [ ] User account exists.
- [ ] Preferences are stored.
- [ ] Trips are stored.
- [ ] Route interactions are stored.
- [ ] Feedback is stored.
- [ ] Segment memory is stored.
- [ ] Twin state is stored.
- [ ] Twin updates after trip evidence.
- [ ] Twin confidence exists.
- [ ] Personalized route scoring uses current twin state.
- [ ] Next trip uses the updated twin.

## Frontend

- [ ] Login.
- [ ] Registration.
- [ ] Dashboard.
- [ ] Route search.
- [ ] Route comparison.
- [ ] Route details.
- [ ] Trip completion.
- [ ] Feedback.
- [ ] History.
- [ ] Preferences.
- [ ] Personalization explanation.

## Engineering

- [ ] PostgreSQL.
- [ ] Database migrations.
- [ ] Authentication.
- [ ] API validation.
- [ ] Unit tests.
- [ ] Integration tests.
- [ ] Git branches.
- [ ] Environment variables.
- [ ] No secrets committed.

## Research

- [ ] Global model evaluation.
- [ ] Time-risk evaluation.
- [ ] Personalization evaluation.
- [ ] Ablation study.
- [ ] Synthetic-data limitations documented.
- [ ] Real-world validation plan documented.
- [ ] Privacy considerations documented.

---

# 72. Final Architecture in One Line

The final SafeRoute system should become:

```text
User
→ Personal Twin
→ Source/Destination/Date/Time
→ Chennai OSM
→ Candidate Routes
→ Crime + Environment + Infrastructure
→ Weather + Traffic + Time
→ Global ML Risk
→ Hybrid Contextual Risk
→ Personal Twin Adjustment
→ Personalized Route Risk
→ Top 5 Routes
→ User Selection
→ Trip History + Feedback
→ Twin Learning
→ Updated Personal Twin
→ Next Trip
```

This is the architecture we should build toward from the current Git checkpoint.


# 53A. Live GPS Navigation — Required Final Feature

The current project already has **turn-by-turn route instructions** generated from OSM route geometry. That functionality stays.

The final system additionally needs **live GPS navigation, route-progress tracking, off-route detection, and dynamic re-routing**.

## Existing navigation

Already implemented:

```text
OSM route geometry
      ↓
Road names
      ↓
Turn detection
      ↓
Turn-by-turn instructions
```

Example:

```text
Head east on General Hospital Road
Turn slight right onto Muthuswamy Bridge
Turn slight left onto Muthuswamy Road
Continue on Napier Bridge
Continue on Kamarajar Salai
Arrive at destination
```

## Required live-navigation layer

```text
TOP 5 ROUTES
     ↓
USER SELECTS ROUTE
     ↓
START NAVIGATION
     ↓
GPS LOCATION
     ↓
MAP MATCHING
     ↓
ROUTE PROGRESS
     ↓
NEXT TURN
     ↓
TURN-BY-TURN GUIDANCE
     ↓
CURRENT TIME / TRAFFIC / WEATHER / RISK / PERSONAL TWIN
     ↓
CONTINUE OR RE-ROUTE
```

---

# 53B. GPS Navigation Flow

```text
Selected Route
      ↓
GPS Tracking
      ↓
Current latitude / longitude
      ↓
Find current route segment
      ↓
Calculate route progress
      ↓
Show next instruction
      ↓
Detect deviation
      ↓
If off-route:
      ↓
Recalculate from CURRENT GPS position
      ↓
Evaluate candidate routes
      ↓
Apply time + traffic + weather + global risk + Personal Twin
      ↓
Select new route
      ↓
Continue navigation
```

The new route must start from the user's **current position**, not the original source.

---

# 53C. GPS Data

The frontend should obtain, where available:

```text
latitude
longitude
timestamp
accuracy
speed
heading
```

Initial browser implementation can use:

```javascript
navigator.geolocation.watchPosition(...)
```

The final mobile implementation should use an appropriate native/background location mechanism.

GPS should primarily support:

```text
live navigation
route progress
off-route detection
re-routing
trip completion
```

Avoid storing second-by-second GPS traces unless they are actually needed for a research purpose.

---

# 53D. Map Matching and Route Progress

The navigation layer needs to determine:

```text
Where is the user?
        ↓
Which OSM segment are they on?
        ↓
Where are they along the selected route?
        ↓
What is the next instruction?
```

Maintain navigation state such as:

```text
current_route_segment
current_instruction_index
distance_to_next_turn
remaining_distance
remaining_route_geometry
```

A proper map-matching approach should be used rather than relying only on raw coordinate distance.

---

# 53E. Off-Route Detection

```text
GPS position
      ↓
Distance / map match to planned route
      ↓
Within threshold?
   /          \
 YES           NO
 ↓              ↓
Continue       Confirm deviation
navigation       ↓
              Off-route
                 ↓
              Re-route
```

Do not re-route because of one noisy GPS reading. Use a short confirmation window or consecutive off-route observations.

---

# 53F. Dynamic Re-Routing

When the user leaves the planned route:

```text
Current GPS
     +
Destination
     ↓
Nearest OSM node
     ↓
Candidate routes
     ↓
Current time
     ↓
Current traffic
     ↓
Current weather
     ↓
Global road risk
     ↓
Personal Twin
     ↓
Personalized risk
     ↓
New route
```

This makes the Personal Twin useful not only during initial route selection, but also during live navigation.

---

# 53G. Re-Routing Due to Changing Conditions

Later, re-routing can also be triggered by meaningful changes such as:

```text
major traffic change
road closure
large risk increase
weather change
manual re-route request
```

GPS updates can happen frequently, but expensive risk/re-routing calculations should **not** run on every GPS update.

Separate:

```text
frequent GPS/progress updates
```

from:

```text
event-triggered risk/re-routing evaluation
```

---

# 53H. Time-Aware Navigation

Time risk becomes dynamic during a trip.

Example:

```text
Trip starts: 6:30 PM
       ↓
7:00 PM
       ↓
7:30 PM
       ↓
8:00 PM
```

The time context changes while travelling.

Therefore the navigation engine should evaluate the **remaining route** using the current time when a meaningful re-evaluation is triggered.

```text
Current GPS
+
Current time
+
Remaining route
      ↓
Current contextual risk
```

---

# 53I. Personal Twin During Navigation

The Personal Twin participates in:

```text
initial route planning
```

and:

```text
live re-routing
```

Example:

```text
User frequently avoids isolated roads
        ↓
User goes off-route
        ↓
Three alternatives available
        ↓
Global risk calculated
        ↓
Personal Twin applied
        ↓
Personalized alternatives
        ↓
New route
```

---

# 53J. Navigation Frontend

Add a dedicated navigation screen containing:

```text
Live map
Current GPS marker
Selected route
Remaining route
Current instruction
Next turn
Distance to next turn
Remaining distance
ETA
Current speed
Route deviation state
Re-routing indicator
End Trip
```

Example:

```text
Turn right onto Rajaji Salai
in 180 m
```

The map should distinguish:

```text
completed route
remaining route
current location
```

---

# 53K. Navigation Backend

Add a dedicated navigation layer instead of putting all navigation logic inside `routes.py`.

Suggested services:

```text
navigation_engine.py
gps_map_matcher.py
rerouting_engine.py
navigation_risk_engine.py
```

Responsibilities:

### `navigation_engine.py`

Maintains:

```text
trip state
route progress
current instruction
remaining route
```

### `gps_map_matcher.py`

Maps:

```text
GPS position → OSM route segment
```

### `rerouting_engine.py`

Handles:

```text
off-route detection
route recalculation
condition-triggered re-routing
```

### `navigation_risk_engine.py`

Evaluates:

```text
remaining route
+
current time
+
current traffic
+
current weather
+
global risk
+
Personal Twin
```

---

# 53L. Navigation APIs

Potential API structure:

```text
POST /api/navigation/start
POST /api/navigation/update
POST /api/navigation/reroute
POST /api/navigation/end
GET  /api/navigation/{trip_id}/state
```

Example GPS update:

```json
{
  "trip_id": "...",
  "latitude": 13.08,
  "longitude": 80.27,
  "accuracy": 8.2,
  "speed": 24.5,
  "heading": 90.0
}
```

Example navigation response:

```json
{
  "instruction": "Turn right onto Rajaji Salai",
  "distance_to_turn_m": 180,
  "remaining_distance_km": 2.4,
  "eta_minutes": 7,
  "off_route": false,
  "rerouting": false
}
```

Exact schemas can be finalized during implementation.

---

# 53M. Final Trip Lifecycle

```text
SEARCH
  ↓
TOP 5 ROUTES
  ↓
SELECT ROUTE
  ↓
START TRIP
  ↓
START GPS NAVIGATION
  ↓
LIVE NAVIGATION
  ↓
TURN-BY-TURN
  ↓
OPTIONAL RE-ROUTING
  ↓
DESTINATION
  ↓
END TRIP
  ↓
TRIP COMPLETED
  ↓
FEEDBACK
  ↓
TWIN LEARNING
```

---

# 53N. GPS Privacy

GPS is sensitive information.

Separate:

```text
temporary live navigation position
```

from:

```text
persisted trip/history data
```

Prefer storing the minimum information needed for:

```text
trip history
personalization
research evaluation
```

Do not expose one user's location/history to another user.

---

# 53O. Navigation Testing

### Normal navigation

```text
Start
→ GPS follows route
→ instructions update
→ destination reached
```

### Off-route

```text
Start
→ leave route
→ deviation confirmed
→ new route generated
→ navigation continues
```

### GPS noise

```text
small GPS variation
→ no unnecessary re-route
```

### Traffic change

```text
route selected
→ traffic changes
→ remaining route evaluated
```

### Time transition

```text
trip starts before evening
→ trip continues into evening/night
→ time-aware risk updated
```

### Personal Twin

```text
learned preference
→ off-route event
→ alternatives generated
→ personalized re-routing
```

---

# 53P. Updated Final Architecture Including Navigation

```text
                         USER
                           │
                    LOGIN / ACCOUNT
                           │
                           ▼
                    PERSONAL TWIN
                           │
SOURCE + DESTINATION + DATE + TIME + MODE
                           │
                           ▼
                       GEOCODER
                           │
                           ▼
                    CHENNAI OSM GRAPH
                           │
                           ▼
                   CANDIDATE ROUTES
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
      CRIME          ENVIRONMENT       INFRASTRUCTURE
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                     TIME CONTEXT
                           │
                     WEATHER CONTEXT
                           │
                     TRAFFIC CONTEXT
                           │
                           ▼
                     GLOBAL LIGHTGBM
                           │
                           ▼
                       ML RISK
                           │
                           ▼
                     HYBRID RISK
                           │
                           ▼
                    TRAFFIC ADJUSTMENT
                           │
                           ▼
                 PERSONAL TWIN ADJUSTMENT
                           │
                           ▼
                PERSONALIZED ROUTE RISK
                           │
                           ▼
                     TOP 5 ROUTES
                           │
                           ▼
                   USER SELECTS ROUTE
                           │
                           ▼
                    START NAVIGATION
                           │
                           ▼
                       GPS TRACKING
                           │
                           ▼
                     MAP MATCHING
                           │
                           ▼
                  TURN-BY-TURN GUIDANCE
                           │
                           ▼
                CURRENT CONDITIONS
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           TIME         TRAFFIC       WEATHER
              │            │            │
              └────────────┼────────────┘
                           ▼
                 REMAINING ROUTE RISK
                           │
                           ▼
                 CONTINUE / RE-ROUTE
                           │
                  ┌────────┴────────┐
                  │                 │
                CONTINUE          RE-ROUTE
                  │                 │
                  │          CURRENT GPS
                  │                 ↓
                  │          CANDIDATE ROUTES
                  │                 ↓
                  │       GLOBAL + PERSONAL RISK
                  │                 ↓
                  │          NEW SAFE ROUTE
                  │                 │
                  └────────┬────────┘
                           ▼
                       DESTINATION
                           │
                           ▼
                      TRIP COMPLETE
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                 HISTORY       FEEDBACK
                    │             │
                    └──────┬──────┘
                           ▼
                    TWIN LEARNING
                           │
                           ▼
                  UPDATED TWIN STATE
                           │
                           └────────────► NEXT TRIP
```

---

# 53Q. Updated Implementation Order

```text
PHASE 1
Current SafeRoute
        ↓
Finish Time-Aware Risk
        ↓
Validate in Colab
        ↓
Backend Integration
        ↓
Frontend Validation

PHASE 2
PostgreSQL
        ↓
Database Models
        ↓
Migrations

PHASE 3
Authentication
        ↓
Register / Login
        ↓
Protected APIs

PHASE 4
Personal Preferences
        ↓
Preference UI
        ↓
Initial Twin

PHASE 5
Trip System
        ↓
Trip creation
        ↓
Route interaction logging
        ↓
History

PHASE 6
Feedback
        ↓
Trip completion
        ↓
Feedback collection

PHASE 7
Personal Twin Learning
        ↓
Segment memory
        ↓
Preference updates
        ↓
Confidence
        ↓
Twin state

PHASE 8
Personalized Route Scoring
        ↓
Global Risk + Personal Twin
        ↓
Personalized Top 5

PHASE 9
LIVE GPS NAVIGATION
        ↓
GPS tracking
        ↓
Map matching
        ↓
Route progress
        ↓
Turn-by-turn navigation
        ↓
Off-route detection
        ↓
Dynamic re-routing
        ↓
Time / traffic / weather updates
        ↓
Personalized re-routing

PHASE 10
Dashboard
        ↓
History
        ↓
Preferences
        ↓
Twin summary
        ↓
Statistics

PHASE 11
Research Evaluation
        ↓
Global vs Time-aware
        ↓
Time-aware vs Personalized
        ↓
Navigation / re-routing evaluation
        ↓
Ablation studies

PHASE 12
Quantum-inspired optimization
        ↓
Research enhancement
```

