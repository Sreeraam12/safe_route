# SafeRoute: Chennai Women's Safe Mobility & Personal Digital Twin System

SafeRoute is an AI-driven, time-aware, personalized safe route recommendation and live GPS navigation platform designed for the metropolitan road network of Chennai, India.

It blends OpenStreetMap road topology, a 35-feature LightGBM environmental and crime risk model, live TomTom traffic intelligence, temporal vulnerability curves, a Personal Digital Twin engine that adapts to user choices, and a real-time turn-by-turn GPS navigation system with automated off-route detection and dynamic re-routing.

---

## Key Capabilities

1. **Metropolitan Chennai Road Network**:
   - High-fidelity OSM graph with 68,667 nodes and 173,935 edges cached locally (`chennai_drive.graphml.xml`) for fast initialization (<10s).
   - Candidate route generation using edge-penalty diversification and overlap control to surface meaningful spatial alternatives.

2. **35-Feature LightGBM Risk Model**:
   - Evaluates crime severity, lighting scores, sidewalk availability, crowd levels, road conditions, police and metro proximity, and weather variables.
   - Operates in conjunction with an empirical contextual risk engine.

3. **Time-Aware Vulnerability Engine**:
   - Models non-linear temporal risk across morning, afternoon, evening, night, and late-night periods.
   - Dynamically scales penalties for isolation, unlit segments, and desolate corridors under nocturnal conditions.

4. **Personal Digital Twin**:
   - Represents individualized safety profiles (e.g. Safety-First, Time-Sensitive, Night-Sensitive).
   - Features persistent Bayesian weight updates from completed trip choices and post-trip feedback.
   - Maintains road-segment memory to build trust or avoidance scores over time.

5. **Live GPS Navigation & Dynamic Re-Routing**:
   - High-precision cross-track error map-matching projecting coordinates onto the active route polyline.
   - Real-time step countdown, distance-to-next-turn, and ETA recalculation.
   - Multi-ping confirmation buffer (50m threshold, 2 pings) preventing spurious off-route alerts.
   - Dynamic re-routing from current GPS position to destination in under 500ms.

6. **Interactive Dashboard & Twin Analytics**:
   - Modern Next.js frontend with live turn guidance HUD, trip history log, user ratings, and active twin parameter visualization.

---

## Architecture Overview

```
                      ┌──────────────────────┐
                      │    USER & TWIN       │
                      │  Adaptive Preferences│
                      └──────────┬───────────┘
                                 │
                     Search: Origin + Dest + Time
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │    CHENNAI OSM       │
                      │  Candidate Generator │
                      └──────────┬───────────┘
                                 ▼
              ┌──────────────────┴──────────────────┐
              │                                     │
              ▼                                     ▼
   ┌──────────────────────┐              ┌──────────────────────┐
   │ 35-Feature LightGBM  │              │ TomTom Live Traffic  │
   │ + Time-Risk Context  │              │ Congestion & Speeds  │
   └──────────┬───────────┘              └──────────┬───────────┘
              │                                     │
              └──────────────────┬──────────────────┘
                                 ▼
                      ┌──────────────────────┐
                      │ Hybrid Risk Scoring  │
                      └──────────┬───────────┘
                                 ▼
                      ┌──────────────────────┐
                      │ Personal Twin Layer  │
                      │ Segment Memory Bias  │
                      └──────────┬───────────┘
                                 ▼
                      ┌──────────────────────┐
                      │ Top 5 Ranked Routes  │
                      └──────────┬───────────┘
                                 ▼
                      ┌──────────────────────┐
                      │ Live GPS Navigation  │
                      │  HUD & Re-Routing    │
                      └──────────┬───────────┘
                                 ▼
                      ┌──────────────────────┐
                      │  Post-Trip Feedback  │
                      │ & Twin State Update  │
                      └──────────────────────┘
```

---

## Directory Structure

```text
safe_route/
├── backend/
│   ├── artifacts/               # LightGBM models, 35 features JSON, hybrid risk pkl
│   ├── app/
│   │   ├── api/                 # FastAPI routes (auth, trips, routes, navigation, users)
│   │   ├── core/                # JWT auth, security, and configuration
│   │   ├── db/                  # SQLAlchemy async session (SQLite & PostgreSQL)
│   │   ├── models/              # Database models (User, Preferences, Trip, Twin, etc.)
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Route engine, ML engine, time risk, twin engine, GPS matcher
│   │   └── main.py              # Application entrypoint
│   └── saferoute.db             # Local SQLite database (or Postgres via DATABASE_URL)
│
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js 16 app router
│   │   ├── components/
│   │   │   ├── auth/            # AuthModal (Sign In / Register)
│   │   │   ├── dashboard/       # DashboardModal (Trip History & Twin Analytics)
│   │   │   ├── feedback/        # TripFeedbackModal
│   │   │   ├── map/             # Leaflet SafeRouteMap with live GPS marker
│   │   │   ├── navigation/      # NavigationHUD (live guidance & GPS simulation)
│   │   │   ├── preferences/     # PreferencesModal (Twin configuration)
│   │   │   ├── routes/          # RouteList and RouteDetails
│   │   │   └── search/          # SearchPanel with departure time picker
│   │   ├── services/            # API client (routeApi.ts)
│   │   └── types/               # TypeScript interfaces
│   └── package.json
│
├── personal_twin_dataset/       # Reference synthetic archetypes & datasets
├── scripts/
│   ├── generate_synthetic_twin_data.py
│   └── evaluate_saferoute.py    # Research benchmarking & ablation script
├── SafeRoute_Final_Architecture_Roadmap.md
└── README.md
```

---

## Quick Start Guide

### 1. Environment Setup

Create and activate a Python 3.12 virtual environment:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
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
```

### 2. Launch Backend Server

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
- Swagger Interactive Documentation: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

### 3. Launch Frontend Application

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## Research Evaluation & Benchmarks

To run the automated empirical benchmark and ablation study:
```bash
python scripts/evaluate_saferoute.py
```
This tests:
- Baseline Dijkstra shortest path vs. Static SafeRoute vs. Night-time contextual routing vs. Personal Twin archetypes.
- Dynamic re-routing execution latency under simulated corridor deviations.
- Generates `evaluation_results.json` and `RESEARCH_EVALUATION_REPORT.md`.

---

## Ethical & Privacy Considerations

- **Synthetic Development Data**: The initial training weights and prototype trip datasets are explicitly synthetic proxies modeled for algorithm evaluation.
- **Privacy by Design**: Sensitive user locations are stored at coarse neighborhood/corridor levels rather than exact home addresses.
- **Explainability**: Every route card provides explicit factor attribution (lighting, isolation, crowd, and past feedback) explaining why an alternative was selected.

