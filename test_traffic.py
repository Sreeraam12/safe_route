import asyncio

from backend.app.services.traffic_engine import get_traffic


async def main():
    traffic = await get_traffic(
        13.0827,
        80.2707,
    )

    print("\nTomTom Traffic")
    print("-------------------------")

    for key, value in traffic.items():
        print(f"{key}: {value}")


asyncio.run(main())