import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

CHENNAI_LANDMARKS = {
    "chennai central": ("Puratchi Thalaivar Dr. M.G. Ramachandran Central Railway Station, Chennai", 13.0827, 80.2750),
    "central": ("Chennai Central, Park Town, Chennai", 13.0827, 80.2750),
    "marina": ("Marina Beach, Triplicane, Chennai", 13.0500, 80.2824),
    "marina beach": ("Marina Beach, Triplicane, Chennai", 13.0500, 80.2824),
    "t nagar": ("T. Nagar, Chennai", 13.0418, 80.2341),
    "t. nagar": ("T. Nagar, Chennai", 13.0418, 80.2341),
    "thyagaraya nagar": ("T. Nagar, Chennai", 13.0418, 80.2341),
    "adyar": ("Adyar, Chennai", 13.0067, 80.2572),
    "guindy": ("Guindy, Chennai", 13.0068, 80.2206),
    "velachery": ("Velachery, Chennai", 12.9784, 80.2180),
    "anna nagar": ("Anna Nagar, Chennai", 13.0850, 80.2101),
    "egmore": ("Egmore, Chennai", 13.0732, 80.2609),
    "mylapore": ("Mylapore, Chennai", 13.0336, 80.2687),
    "nungambakkam": ("Nungambakkam, Chennai", 13.0604, 80.2425),
    "saidapet": ("Saidapet, Chennai", 13.0213, 80.2231),
    "thiruvanmiyur": ("Thiruvanmiyur, Chennai", 12.9830, 80.2594),
    "taramani": ("Taramani, Chennai", 12.9863, 80.2432),
    "kotturpuram": ("Kotturpuram, Chennai", 13.0169, 80.2417),
    "vadapalani": ("Vadapalani, Chennai", 13.0500, 80.2121),
    "koyambedu": ("Koyambedu, Chennai", 13.0694, 80.1948),
    "tambaram": ("Tambaram, Chennai", 12.9249, 80.1000),
    "chromepet": ("Chromepet, Chennai", 12.9516, 80.1462),
    "porur": ("Porur, Chennai", 13.0382, 80.1565),
    "perambur": ("Perambur, Chennai", 13.1143, 80.2366),
    "vepery": ("Vepery, Chennai", 13.0853, 80.2642),
    "triplicane": ("Triplicane, Chennai", 13.0588, 80.2756),
    "royapettah": ("Royapettah, Chennai", 13.0553, 80.2642),
    "alwarpet": ("Alwarpet, Chennai", 13.0335, 80.2531),
    "besant nagar": ("Besant Nagar, Chennai", 13.0003, 80.2667),
    "omr": ("Old Mahabalipuram Road (OMR), Taramani, Chennai", 12.9716, 80.2431),
    "ecr": ("East Coast Road (ECR), Thiruvanmiyur, Chennai", 12.9654, 80.2598),
}


def _match_local_chennai_place(place: str):
    key = place.strip().lower().replace(",", " ").strip()
    if key in CHENNAI_LANDMARKS:
        name, lat, lon = CHENNAI_LANDMARKS[key]
        return {"name": name, "latitude": lat, "longitude": lon}
    for k, (name, lat, lon) in CHENNAI_LANDMARKS.items():
        if k in key or key in k:
            return {"name": name, "latitude": lat, "longitude": lon}
    return None


async def geocode_place(place: str):
    # 1. Instant local match for known Chennai places (prevents Nominatim rate-limits/timeouts)
    local_hit = _match_local_chennai_place(place)
    if local_hit:
        return local_hit

    params = {
        "q": f"{place}, Chennai, Tamil Nadu, India",
        "format": "json",
        "limit": 1,
    }
    headers = {"User-Agent": "SafeRoute/1.0"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                NOMINATIM_URL,
                params=params,
                headers=headers,
                timeout=4.0,
            )
        response.raise_for_status()
        results = response.json()
        if results:
            result = results[0]
            return {
                "name": result["display_name"],
                "latitude": float(result["lat"]),
                "longitude": float(result["lon"]),
            }
    except Exception:
        pass

    if local_hit:
        return local_hit

    # Final fallback within central Chennai so routing never crashes on network timeout
    return {
        "name": f"{place.strip()}, Chennai, Tamil Nadu, India",
        "latitude": 13.0418,
        "longitude": 80.2341,
    }
