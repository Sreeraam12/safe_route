# SafeRoute: Chennai Women's Safe Mobility, Personal Digital Twin & Emergency SOS System

SafeRoute is an AI-driven, time-aware, personalized safe route recommendation, live turn-by-turn GPS navigation, and real-time emergency SOS platform engineered for the metropolitan road network of Chennai, India.

It unifies OpenStreetMap (OSM) road topology, a 35-feature LightGBM environmental and crime risk model, live TomTom traffic intelligence, non-linear temporal vulnerability curves, an adaptive **Personal Digital Twin** that learns from both route selections and post-trip user feedback, a real-time **GPS map-matching & dynamic re-routing engine**, and an integrated **Emergency SOS & Incident Response subsystem** with live guardian tracking, Chennai Police Station Haversine dispatch, and real-time corridor risk updates.

---

## Key Capabilities

1. **Metropolitan Chennai Road Network & Resilient Geocoding**:
   - High-fidelity OSM road network (`chennai_drive.graphml.xml`) with **68,667 nodes** and **173,935 directed road edges** cached locally for rapid startup (<10s).
   - Multi-route candidate generation using iterative edge-penalty diversification and overlap control to surface distinct, meaningful spatial alternatives (Safest, Balanced, Fastest, Well-Lit, Main Roads).
   - **Resilient Dual-Stage Geocoder**: Pairs OpenStreetMap Nominatim HTTP geocoding with an instant local Chennai landmark coordinate dictionary (covering 20+ hubs such as T. Nagar, Adyar, Anna Nagar, Velachery, Guindy, Tambaram, OMR, Mylapore, Egmore, Marina Beach, etc.) so route searches succeed even during external network timeouts.

2. **35-Feature LightGBM Risk Model & Real-Time Incident Overlay**:
   - Evaluates 35 road-segment attributes including historical crime severity, street lighting density, CCTV coverage, sidewalk availability, commercial crowd levels, road classification, police station/metro proximity, and weather variables.
   - Dynamically overlays active `SafetyEvent` alerts (such as recent SOS distress triggers or community hazards) with confidence-weighted decay (`severity * confidence`) so routes automatically steer around active incident corridors.

3. **Time-Aware Vulnerability Engine & Live TomTom Traffic**:
   - Models non-linear temporal risk across **Morning**, **Afternoon**, **Evening**, **Night**, and **Late-Night** windows.
   - Dynamically scales penalties for road isolation, unlit segments, and low-crowd corridors during dark hours.
   - Integrates live **TomTom Traffic Flow API** segment speeds and congestion ratios with automatic offline speed-model fallback.

4. **Personal Digital Twin & Post-Trip Feedback Loop**:
   - Maintains an individualized safety profile (`personal_preferences` + `personal_twin_state`) initialized via user archetypes (e.g., *Safety-First*, *Night-Caution*, *Balanced*, *Time-Conscious*).
   - **Two-Stage Adaptation**:
     1. **Revealed Preference Update**: When a user selects a candidate route over alternatives, the Twin compares the chosen route's attributes against rejected alternatives and shifts weights toward the user's revealed priority.
     2. **Post-Trip Explicit Feedback (`TripFeedbackModal`)**: Upon arriving at the destination, the user rates overall trip safety (1?5 stars), comfort level, lighting/crowd conditions, and specific concern tags (`poor_lighting`, `isolated_stretch`, `suspicious_activity`, `high_traffic`). The Twin updates both global preference weights and **segment-level memory bias** to avoid uncomfortable streets on future journeys.

5. **Live GPS Navigation & Dynamic Off-Route Re-Routing**:
   - High-precision cross-track error map-matching (`gps_matcher.py`) projecting live GPS coordinates onto the active route polyline.
   - Real-time step countdown, distance-to-next-turn, voice/visual maneuver guidance, and live ETA recalculation in `NavigationHUD.tsx`.
   - Multi-ping confirmation buffer (**50m cross-track threshold across 2 consecutive GPS pings**) preventing false off-route triggers from GPS jitter.
   - Automated sub-500ms safe route recalculation from the user's live coordinates when a true route deviation is confirmed.

6. **Emergency SOS, Trusted Contact Dispatch & Live Guardian Tracking**:
   - **Trusted Contacts Onboarding & Management**: Users register emergency contacts during sign-up (`LoginPage.tsx`) or manage them anytime via the **??? Profile & Contacts** modal (`EmergencyModal.tsx`), enforced with strict 10-digit numeric phone validation (`^\d{10}$`).
   - **1-Click SOS Trigger (`NavigationHUD.tsx`)**:
     - Immediately **freezes navigation movement** at the exact distress coordinates until the user explicitly cancels or resolves the SOS.
     - Snaps GPS coordinates to the nearest OSM street segment (`road_name`) and locates the **nearest Greater Chennai Police Station** via Haversine distance (`police_station_service.py`).
     - Generates a cryptographic live tracking link (`/sos/track/[token]`) and logs alerts to all active trusted contacts (`sos_notifications`), complete with 1-click **SMS**, **WhatsApp**, **Share Live Link**, and **Call 112** dispatch buttons.
     - Injects a temporary 24-hour unverified `SafetyEvent` (`confidence=0.30`) on the affected corridor to warn other SafeRoute travellers in real time.

---

## System Architecture & End-to-End Data Flow

```text
                      ????????????????????????????????????????????
                      ?         USER, AUTH & TRUSTED CONTACTS    ?
                      ?   JWT Auth + 10-Digit Validated Contacts ?
                      ????????????????????????????????????????????
                                           ?
                               Search: Origin + Dest + Time
                                           ?
                                           ?
                      ????????????????????????????????????????????
                      ?     RESILIENT GEOCODER & CHENNAI OSM     ?
                      ?  Nominatim + Local Landmark Fallback     ?
                      ?  68,667 Nodes / 173,935 Edges Graph      ?
                      ????????????????????????????????????????????
                                           ?
        ???????????????????????????????????????????????????????????????????????
        ?                                  ?                                  ?
        ?                                  ?                                  ?
??????????????????????          ??????????????????????             ??????????????????????
? 35-Feature LightGBM?          ? Time-Risk & Active ?             ? TomTom Live Traffic?
? Base Safety Scorer ?          ? SafetyEvents Layer ?             ? + Offline Fallback ?
??????????????????????          ??????????????????????             ??????????????????????
          ?                                ?                                  ?
          ?????????????????????????????????????????????????????????????????????
                                           ?
                      ????????????????????????????????????????????
                      ?         PERSONAL DIGITAL TWIN LAYER      ?
                      ?  Adaptive Weights + Road Segment Memory  ?
                      ????????????????????????????????????????????
                                           ?
                      ????????????????????????????????????????????
                      ?       TOP RANKED CANDIDATE ROUTES        ?
                      ?  Explainable Attribution & Risk Badges   ?
                      ????????????????????????????????????????????
                                           ?
                      ????????????????????????????????????????????
                      ?        LIVE GPS NAVIGATION HUD           ?
                      ?  Map-Matching + 50m Off-Route Rerouting  ?
                      ????????????????????????????????????????????
                                ?                      ?
               Normal Arrival   ?                      ?  Emergency SOS Triggered
                                ?                      ?
          ?????????????????????????????    ????????????????????????????????????????
          ?  POST-TRIP FEEDBACK MODAL ?    ?       EMERGENCY SOS ENGINE           ?
          ?  1-5? Rating & Issue Tags ?    ? ? Halts Navigation Movement          ?
          ?  Updates Twin Weights &   ?    ? ? Nearest Chennai Police (Haversine) ?
          ?  Corridor Memory Bias     ?    ? ? Trusted Contact SMS / WhatsApp     ?
          ?????????????????????????????    ? ? Live Tracking (/sos/track/[token]) ?
                                           ? ? 24h Temporary SafetyEvent Penalty  ?
                                           ????????????????????????????????????????
```

---

## Detailed Working of Each Subsystem

### 1. Resilient Geocoding & Candidate Route Generation
- **Dual-Stage Geocoding (`backend/app/services/geocoder.py`)**:
  - When a user enters an origin or destination (e.g., `"T. Nagar"` to `"Adyar"`), the geocoder first checks a curated fast-lookup table of 20+ major Chennai hubs and neighborhoods.
  - For arbitrary street addresses, it queries OpenStreetMap Nominatim bounded to the Greater Chennai bounding box (`12.85?N?13.25?N, 80.10?E?80.35?E`) with automatic `httpx` timeout handling and fallback so network drops never cause HTTP 500 errors.
- **Diversified Candidate Path Search (`backend/app/services/route_engine.py`)**:
  - Snaps origin and destination `(lat, lon)` to the nearest nodes in the in-memory NetworkX `MultiDiGraph`.
  - Runs multiple weighted shortest-path passes (Optimizing for *Max Safety*, *Balanced Utility*, *Shortest Time*, *Well-Lit Corridors*, and *Main Arterial Roads*).
  - Applies a 35% edge-weight penalty to edges already used in prior candidates and enforces a maximum path-overlap filter (<85% shared edges) so the user is presented with genuinely distinct physical routes across Chennai.

### 2. Multi-Factor Time-Aware Safety Scoring
For every road edge $e$ along a candidate route at departure hour $t$, SafeRoute computes a composite edge risk $R(e, t)$:

$$R(e, t) = w_{	ext{ml}} \cdot S_{	ext{LightGBM}}(e) + w_{	ext{time}}(t) \cdot \Phi_{	ext{temporal}}(e, t) + w_{	ext{twin}} \cdot \Psi_{	ext{twin}}(e, u) + \Delta_{	ext{SOS}}(e, t)$$

1. **Base ML Risk $S_{	ext{LightGBM}}(e)$ (`ml_engine.py`)**: Inferred by the trained 35-feature LightGBM model over static and semi-dynamic street features (crime rate, lighting index, CCTV presence, police distance, road width, crowd density).
2. **Temporal Vulnerability $\Phi_{	ext{temporal}}(e, t)$ (`time_risk_engine.py`)**: Applies non-linear multipliers based on time of day:
   - *Daytime (06:00?17:59)*: Standard baseline weights.
   - *Evening (18:00?20:59)*: $1.35	imes$ penalty on poorly lit segments.
   - *Night (21:00?23:59)*: $1.75	imes$ penalty on unlit/isolated streets; $1.4	imes$ bonus for commercial/CCTV corridors.
   - *Late Night (00:00?05:59)*: $2.20	imes$ penalty on isolated segments and minor residential alleys.
3. **Personal Twin Bias $\Psi_{	ext{twin}}(e, u)$ (`twin_engine.py`)**: Incorporates user $u$'s personalized weight vector (`lighting_weight`, `crowd_weight`, `police_proximity_weight`, `isolation_penalty_weight`, `traffic_weight`) and historical segment memory (`segment_memory_json`).
4. **Live Incident Overlay $\Delta_{	ext{SOS}}(e, t)$ (`sos_engine.py`)**: Queries active, non-expired `SafetyEvent` records within ~300m (`?0.003?` lat/lon bounding box) of the route and subtracts `severity * confidence * 2.5` from the safety score (capped at 15 points for unverified triggers) to dynamically route around active emergencies.

### 3. Personal Digital Twin & Post-Trip Feedback Adaptation
- **Twin Initialization**: Every registered user receives a `PersonalPreference` row and a `PersonalTwinState` row tracking their dynamic weights, adaptation count, and segment-level comfort memory.
- **Implicit Learning (Route Choice)**: When the user starts navigation on Route $i$ out of $\{1 \dots k\}$ candidates (`POST /api/trips/start`), `twin_engine.update_from_route_selection()` compares Route $i$'s feature averages against the mean of rejected routes and performs a bounded learning-rate step ($\eta = 0.05$).
- **Explicit Learning (Post-Trip Feedback)**:
  - When the user clicks **End Trip** or arrives at the destination, `TripFeedbackModal.tsx` prompts for:
    - Overall Safety Rating (`1` to `5` stars)
    - Felt Safe toggle (`true` / `false`)
    - Contextual tags (`poor_lighting`, `isolated_stretch`, `high_traffic`, `suspicious_activity`, `smooth_safe_corridor`)
  - Submitting calls `POST /api/trips/feedback`, which persists a `RouteFeedback` record and updates `PersonalTwinState`:
    - Low ratings (`<= 2`) with `poor_lighting` or `isolated_stretch` boost `lighting_weight` and `isolation_penalty_weight` by $+0.08$ and record negative trust scores on the traversed road segments.
    - High ratings (`>= 4`) reinforce current Twin weights and boost positive trust scores for those corridors.

### 4. Live GPS Navigation & Dynamic Re-Routing
- **Simulation & Real Geolocation (`NavigationHUD.tsx`)**:
  - Supports both real browser `navigator.geolocation` and an interactive on-road GPS simulator that steps along the route geometry while streaming `POST /api/navigation/gps-update` every 2 seconds.
- **Map-Matching & Deviation Buffer (`gps_matcher.py`)**:
  - Projects the user's `(lat, lon)` orthogonally onto every polyline segment of the active route to compute exact cross-track distance in meters, remaining distance, and next turn instruction.
  - If cross-track error exceeds **50 meters** for **2 consecutive GPS pings**, the backend sets `re_route_needed = true` and returns a newly calculated safest route from the user's current coordinates to the destination.

### 5. Emergency SOS & Incident Response Subsystem
The SOS subsystem provides immediate protection during live navigation and anywhere in the app:

1. **Trusted Contacts & Strict Phone Validation**:
   - Users can add trusted contacts during registration (`LoginPage.tsx`) or inside the **??? Profile & Contacts** dashboard (`EmergencyModal.tsx`).
   - Both frontend and backend (`schemas/sos.py` & `schemas/user.py`) enforce a strict 10-digit numeric regex (`^\d{10}$`), stripping spaces/hyphens and rejecting non-numeric or invalid-length phone numbers.

2. **SOS Activation Flow (`POST /api/sos/activate`)**:
   - **Immediate Navigation Freeze**: As soon as the user presses **?? EMERGENCY SOS** in `NavigationHUD.tsx`, the simulation/navigation loop halts (`!activeSOS` guard) so the user's marker stays locked at the exact emergency coordinates until the user clicks **Cancel SOS** or **Mark Safe**.
   - **OSM Corridor Snapping**: Snaps `(lat, lon)` to the nearest graph edge in `route_engine.graph` to identify the exact street name (e.g., *Anna Salai*, *Sardar Patel Road*).
   - **Nearest Police Station Lookup (`police_station_service.py`)**: Computes Haversine distance against 18 major Greater Chennai Police Stations (T. Nagar R-1, Adyar J-2, Mylapore E-1, Anna Nagar K-4, Guindy J-3, Velachery J-7, Egmore F-2, Kotturpuram J-4, Triplicane D-1, etc.) and returns the closest station's name, phone number, address, and distance in km.
   - **Multi-Channel Guardian Dispatch (`notification_service.py`)**:
     - Creates an `SOSEvent` with a unique `share_token` and live tracking URL (`/sos/track/[token]`).
     - Logs notification payloads for all active `TrustedContact` records in `sos_notifications` (and automatically dispatches real SMS if `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` are configured in `.env`).
     - Displays instant 1-click **?? SMS** (`sms:<phones>?body=...`), **?? WhatsApp** (`https://wa.me/91<phone>?text=...`), **?? Share Live Link** (Web Share API + clipboard fallback), and **?? Call 112** action buttons in the red emergency HUD banner.
   - **Temporary Corridor Safety Penalty**: Inserts an unverified `SafetyEvent` (`event_type="SOS_ALERT"`, `severity=4`, `confidence=0.30`, `expires_at=+24h`) so concurrent route searches avoid the distress stretch.

3. **Live Guardian Tracking (`/sos/track/[token]`) & Resolution (`POST /api/sos/resolve`)**:
   - Family members opening the tracking link see an auto-refreshing (every 5s) emergency dashboard showing the user's live coordinates, corridor name, battery level, nearest police station details, GPS breadcrumb trail, and direct Google Maps directions.
   - When the user clicks **Mark Safe** (`SAFE`) or **Cancel SOS** (`FALSE_ALARM`), the `SOSEvent` is closed, any false-alarm `SafetyEvent` penalty is immediately deactivated (`expires_at = now`), and live navigation movement seamlessly resumes.

---

## Database Schema (10 Async SQLAlchemy Tables)

SafeRoute uses an async SQLAlchemy ORM layer (`backend/app/db/database.py`) supporting both local SQLite (`aiosqlite`) and production PostgreSQL (`asyncpg`):

| Table Name | Model File | Primary Purpose |
| :--- | :--- | :--- |
| `users` | `models/user.py` | User credentials, profile details, phone number, and home/work locations. |
| `personal_preferences` | `models/user.py` | Explicit user slider weights (lighting, crowd, police proximity, isolation, traffic). |
| `personal_twin_state` | `models/user.py` | Adaptive Bayesian Twin weights, archetype label, adaptation count, and JSON segment memory. |
| `trips` | `models/trip.py` | Active and historical trips, origin/destination coordinates, chosen route geometry, and status. |
| `route_feedback` | `models/trip.py` | Post-trip 1?5? safety ratings, `felt_safe` boolean, issue tags, and qualitative comments. |
| `trusted_contacts` | `models/trusted_contact.py` | User's emergency guardians (`name`, 10-digit `phone_number`, `relationship_type`, `priority_order`, `is_active`). |
| `sos_events` | `models/sos.py` | Master emergency incident record (`status`, `lat`, `lon`, `road_name`, `nearest_police_station`, `share_token`). |
| `sos_location_updates` | `models/sos.py` | Time-series GPS breadcrumb trail (`lat`, `lon`, `speed`, `heading`, `battery_level`) during an active SOS. |
| `sos_notifications` | `models/sos.py` | Audit trail of SMS/WhatsApp/In-App alerts dispatched to each `TrustedContact`. |
| `safety_events` | `models/sos.py` | Time-decaying spatial risk events (`SOS_ALERT`, `USER_REPORT`) with `severity`, `confidence`, and `expires_at`. |

---

## REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **Auth & Twin** | | |
| `POST` | `/api/auth/register` | Register a new user, initialize Twin archetype, and onboard optional `trusted_contacts`. |
| `POST` | `/api/auth/login` | Authenticate user and return a signed JWT access token. |
| `GET` | `/api/users/me/twin` | Fetch the user's current Personal Digital Twin state, weights, and recent trip stats. |
| `PUT` | `/api/users/me/preferences` | Update explicit safety vs. travel-time preference sliders. |
| **Safe Routing & Navigation** | | |
| `POST` | `/api/routes/search` | Generate top ranked safe routes with ML risk, time-of-day context, traffic, and Twin scoring. |
| `POST` | `/api/navigation/gps-update` | Map-match live GPS coordinates, compute turn countdown, and trigger dynamic off-route re-routing. |
| `POST` | `/api/trips/start` | Record trip start and trigger implicit Revealed Preference Twin weight adaptation. |
| `POST` | `/api/trips/feedback` | Submit post-trip safety rating & tags to update Twin weights and corridor memory. |
| **Emergency SOS & Trusted Contacts** | | |
| `GET` / `POST` | `/api/emergency/contacts` | List or create validated 10-digit trusted emergency contacts. |
| `PUT` / `DELETE` | `/api/emergency/contacts/{id}` | Update or remove a trusted emergency contact. |
| `POST` | `/api/sos/activate` | Trigger an active SOS alert, snap to OSM road, locate nearest police station, and alert contacts. |
| `POST` | `/api/sos/update-location` | Append a live GPS & battery breadcrumb to an active SOS event. |
| `POST` | `/api/sos/resolve` | Resolve an active SOS (`SAFE` or `FALSE_ALARM`) and resume normal navigation. |
| `GET` | `/api/sos/track/{share_token}` | Public endpoint powering the live guardian tracking page (`/sos/track/[token]`). |
| `GET` | `/api/sos/history` | Fetch the authenticated user's historical SOS activations and resolutions. |

---

## Directory Structure

```text
safe_route/
??? backend/
?   ??? artifacts/               # LightGBM models, 35 features JSON, hybrid risk pkl
?   ??? app/
?   ?   ??? api/                 # FastAPI routers (auth, routes, navigation, trips, users, sos, sos_routes)
?   ?   ??? core/                # JWT authentication, password hashing, and configuration
?   ?   ??? db/                  # SQLAlchemy async engine & session management
?   ?   ??? models/              # ORM models (user.py, trip.py, trusted_contact.py, sos.py)
?   ?   ??? schemas/             # Pydantic validation schemas (user.py, route.py, sos.py)
?   ?   ??? services/            # Core engines:
?   ?   ?   ??? route_engine.py          # OSM graph, candidate routing & risk aggregation
?   ?   ?   ??? ml_engine.py             # 35-feature LightGBM inference
?   ?   ?   ??? time_risk_engine.py      # Temporal vulnerability multipliers
?   ?   ?   ??? twin_engine.py           # Personal Digital Twin & feedback learning
?   ?   ?   ??? traffic_engine.py        # TomTom live traffic & offline fallback
?   ?   ?   ??? geocoder.py              # Nominatim + Chennai landmark fallback geocoder
?   ?   ?   ??? gps_matcher.py           # Polyline projection & off-route detection
?   ?   ?   ??? sos_engine.py            # SOS activation, tracking & SafetyEvent decay
?   ?   ?   ??? police_station_service.py# 18 Chennai Police Stations Haversine matcher
?   ?   ?   ??? notification_service.py  # Trusted contact SMS/WhatsApp/in-app dispatch
?   ?   ??? main.py              # FastAPI application entrypoint & table auto-creation
?   ??? saferoute.db             # Local SQLite database (or Postgres via DATABASE_URL)
?
??? frontend/
?   ??? src/
?   ?   ??? app/
?   ?   ?   ??? page.tsx                 # Main SafeRoute application shell
?   ?   ?   ??? sos/track/[token]/       # Public live emergency tracking page for guardians
?   ?   ??? components/
?   ?   ?   ??? auth/                    # LoginPage (Sign In, Register & Contact Onboarding)
?   ?   ?   ??? dashboard/               # DashboardModal (Trip History & Twin Analytics)
?   ?   ?   ??? emergency/               # EmergencyModal (Trusted Contacts CRUD & SOS History)
?   ?   ?   ??? feedback/                # TripFeedbackModal (Post-trip safety & tag feedback)
?   ?   ?   ??? map/                   a  # Leaflet SafeRouteMap with live GPS & SOS markers
?   ?   ?   ??? navigation/              # NavigationHUD (Turn guidance, simulation & SOS banner)
?   ?   ?   ??? preferences/             # PreferencesModal (Explicit Twin weight sliders)
?   ?   ?   ??? routes/                  # RouteList and RouteDetails cards
?   ?   ?   ??? search/                  # SearchPanel with departure time selector
?   ?   ??? services/                    # Typed API client (routeApi.ts)
?   ?   ??? types/                       # TypeScript interfaces
?   ??? package.json
?
??? personal_twin_dataset/       # Synthetic user archetypes & evaluation datasets
??? scripts/
?   ??? generate_synthetic_twin_data.py
?   ??? evaluate_saferoute.py    # Empirical benchmarking & ablation suite
??? SOS_plan.md                  # Emergency SOS subsystem architectural specification
??? SafeRoute_Final_Architecture_Roadmap.md
??? README.md
```

---

## Quick Start Guide

### 1. Environment Setup

Create and activate a Python 3.12 virtual environment:
```bash
python -m venv .venv
# On Windows:
.venv\Scriptsctivate
# On Linux/macOS:
source .venv/bin/activate
```

Install backend dependencies:
```bash
pip install -r backend/requirements.txt
# Key packages: fastapi uvicorn sqlalchemy aiosqlite asyncpg pyjwt bcrypt osmnx lightgbm networkx httpx
```

Configure environment variables in `.env`:
```env
DATABASE_URL=sqlite+aiosqlite:///backend/saferoute.db
JWT_SECRET=saferoute_super_secret_jwt_key_chennai_2026
TOMTOM_API_KEY=your_tomtom_api_key_here
FRONTEND_BASE_URL=http://localhost:3000
# Optional Twilio SMS credentials for automated carrier SMS dispatch:
# TWILIO_ACCOUNT_SID=your_twilio_sid
# TWILIO_AUTH_TOKEN=your_twilio_token
# TWILIO_FROM_NUMBER=+1234567890
```

### 2. Launch Backend Server

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
- Swagger Interactive Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 3. Launch Frontend Application

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` (or your LAN IP on mobile devices) in your browser.

---

## Research Evaluation & Benchmarks

To run the automated empirical benchmark and ablation study:
```bash
python scripts/evaluate_saferoute.py
```
This evaluates:
- Baseline Dijkstra shortest path vs. Static SafeRoute vs. Night-time contextual routing vs. Personal Twin archetypes.
- Dynamic re-routing execution latency under simulated corridor deviations.
- Generates `evaluation_results.json` and `RESEARCH_EVALUATION_REPORT.md`.

---

## Ethical & Privacy Considerations

- **Bounded Unverified Incident Impact**: SOS alerts and user-reported hazards are ingested with a low initial confidence (`0.30`) and an automatic 24-hour expiration window so unverified reports warn nearby travellers without permanently skewing the core LightGBM safety model.
- **Privacy by Design**: Live tracking links (`/sos/track/[token]`) use high-entropy cryptographic tokens and only expose live location breadcrumbs while an SOS event is actively open.
- **Explainable Recommendations**: Every route card provides explicit factor attribution (lighting, isolation, crowd density, active incident penalties, and Personal Twin alignment) explaining why an alternative corridor was recommended.
