import math
from typing import Dict, Any, Tuple, Optional

try:
    from backend.app.services.route_engine import GRAPH, get_nearest_node as find_nearest_node
except Exception:
    GRAPH, find_nearest_node = None, None


CHENNAI_POLICE_STATIONS = [
    {"name": "J-1 Saidapet Police Station", "lat": 13.0213, "lon": 80.2231, "phone": "112 / 044-23452359"},
    {"name": "J-2 Adyar Police Station", "lat": 13.0067, "lon": 80.2572, "phone": "112 / 044-23452360"},
    {"name": "J-3 Guindy Police Station", "lat": 13.0068, "lon": 80.2206, "phone": "112 / 044-23452361"},
    {"name": "J-4 Kotturpuram Police Station", "lat": 13.0169, "lon": 80.2417, "phone": "112 / 044-23452362"},
    {"name": "J-6 Thiruvanmiyur Police Station", "lat": 12.9830, "lon": 80.2594, "phone": "112 / 044-23452363"},
    {"name": "J-7 Velachery Police Station", "lat": 12.9784, "lon": 80.2180, "phone": "112 / 044-23452364"},
    {"name": "R-1 Mambalam (T. Nagar) Police Station", "lat": 13.0418, "lon": 80.2341, "phone": "112 / 044-23452365"},
    {"name": "R-4 Soundarapandianar Angadi Police Station", "lat": 13.0405, "lon": 80.2412, "phone": "112 / 044-23452366"},
    {"name": "E-1 Mylapore Police Station", "lat": 13.0336, "lon": 80.2687, "phone": "112 / 044-23452367"},
    {"name": "F-1 Chintadripet Police Station", "lat": 13.0756, "lon": 80.2715, "phone": "112 / 044-23452368"},
    {"name": "F-3 Nungambakkam Police Station", "lat": 13.0604, "lon": 80.2425, "phone": "112 / 044-23452369"},
    {"name": "K-4 Anna Nagar Police Station", "lat": 13.0850, "lon": 80.2101, "phone": "112 / 044-23452370"},
    {"name": "G-1 Vepery Police Station", "lat": 13.0853, "lon": 80.2642, "phone": "112 / 044-23452371"},
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearest_police_station(lat: float, lon: float) -> Dict[str, Any]:
    best = None
    best_dist = 999999.0
    for st in CHENNAI_POLICE_STATIONS:
        d = haversine_km(lat, lon, st["lat"], st["lon"])
        if d < best_dist:
            best_dist = d
            best = st
    return {
        "name": best["name"] if best else "Chennai City Police Control Room",
        "lat": best["lat"] if best else 13.0827,
        "lon": best["lon"] if best else 80.2707,
        "distance_km": round(best_dist, 2) if best else 0.0,
        "phone": best.get("phone", "112 / 044-23452359") if best else "112 / 044-23452359",
    }


def identify_current_road_segment(lat: float, lon: float) -> Tuple[Optional[str], str]:
    try:
        if GRAPH is not None and find_nearest_node is not None:
            node_id = find_nearest_node(GRAPH, lat, lon)
            edges = list(GRAPH.edges(node_id, data=True))
            if edges:
                u, v, data = edges[0]
                road_name = data.get("name", "Chennai Arterial Road")
                if isinstance(road_name, list):
                    road_name = road_name[0]
                return f"{u}-{v}", str(road_name)
    except Exception:
        pass
    return "seg-chennai", "Chennai Monitored Road Corridor"
