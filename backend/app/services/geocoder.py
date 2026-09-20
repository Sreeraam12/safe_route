import httpx


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


async def geocode_place(place: str):
    params = {
        "q": f"{place}, Chennai, Tamil Nadu, India",
        "format": "json",
        "limit": 1,
    }

    headers = {
        "User-Agent": "SafeRoute/1.0"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=10.0,
        )

    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    result = results[0]

    return {
        "name": result["display_name"],
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
    }