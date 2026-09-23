"use client";

import {
  MapContainer,
  TileLayer,
  Polyline,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import { useEffect } from "react";
import L from "leaflet";
import type { RouteResult } from "../../types/route";

interface LocationPoint {
  name: string;
  latitude: number;
  longitude: number;
}

interface SafeRouteMapProps {
  routes: RouteResult[];
  selectedRouteIndex: number | null;
  source: LocationPoint | null;
  destination: LocationPoint | null;
  userLocation?: [number, number] | null;
}

const ROUTE_COLORS = [
  "#16a34a",
  "#2563eb",
  "#9333ea",
  "#ea580c",
  "#dc2626",
];

// Custom HTML/SVG Markers to avoid missing Leaflet asset URLs
function createSourceIcon() {
  return L.divIcon({
    className: "saferoute-source-pin",
    html: `
      <div style="position: relative; width: 36px; height: 44px; display: flex; flex-direction: column; align-items: center;">
        <div style="width: 34px; height: 34px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 50% 50% 50% 0; transform: rotate(-45deg); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(16,185,129,0.5); border: 2.5px solid #ffffff;">
          <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="transform: rotate(45deg); width: 17px; height: 17px;">
            <circle cx="12" cy="12" r="3.5" fill="#ffffff" />
            <path d="M12 2v3m0 14v3M2 12h3m14 0h3" />
          </svg>
        </div>
        <div style="width: 12px; height: 4px; background: rgba(0,0,0,0.25); border-radius: 50%; margin-top: 4px; filter: blur(0.5px);"></div>
      </div>
    `,
    iconSize: [36, 44],
    iconAnchor: [18, 42],
    popupAnchor: [0, -38],
  });
}

function createDestIcon() {
  return L.divIcon({
    className: "saferoute-dest-pin",
    html: `
      <div style="position: relative; width: 36px; height: 44px; display: flex; flex-direction: column; align-items: center;">
        <div style="width: 34px; height: 34px; background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); border-radius: 50% 50% 50% 0; transform: rotate(-45deg); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(239,68,68,0.5); border: 2.5px solid #ffffff;">
          <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="transform: rotate(45deg); width: 17px; height: 17px;">
            <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" fill="#ffffff" />
            <line x1="4" y1="22" x2="4" y2="15" stroke-width="2.5" />
          </svg>
        </div>
        <div style="width: 12px; height: 4px; background: rgba(0,0,0,0.25); border-radius: 50%; margin-top: 4px; filter: blur(0.5px);"></div>
      </div>
    `,
    iconSize: [36, 44],
    iconAnchor: [18, 42],
    popupAnchor: [0, -38],
  });
}

function createUserLocationIcon() {
  return L.divIcon({
    className: "saferoute-gps-pin",
    html: `
      <div style="position: relative; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">
        <div style="position: absolute; width: 28px; height: 28px; border-radius: 50%; background: rgba(59,130,246,0.35); animation: ping 1.5s cubic-bezier(0,0,0.2,1) infinite;"></div>
        <div style="width: 16px; height: 16px; border-radius: 50%; background: #2563eb; border: 3px solid #ffffff; box-shadow: 0 2px 8px rgba(37,99,235,0.6);"></div>
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  });
}

function MapController({
  route,
  source,
  destination,
}: {
  route: RouteResult | null;
  source: LocationPoint | null;
  destination: LocationPoint | null;
}) {
  const map = useMap();

  useEffect(() => {
    if (route && route.geometry.length > 0) {
      const positions = route.geometry.map(
        ([longitude, latitude]) =>
          [latitude, longitude] as [number, number]
      );

      map.fitBounds(positions, {
        padding: [70, 70],
        maxZoom: 15,
      });
    } else if (source && destination) {
      map.fitBounds(
        [
          [source.latitude, source.longitude],
          [destination.latitude, destination.longitude],
        ],
        {
          padding: [90, 90],
          maxZoom: 15,
        }
      );
    } else if (source) {
      map.setView([source.latitude, source.longitude], 14);
    } else if (destination) {
      map.setView([destination.latitude, destination.longitude], 14);
    }
  }, [map, route, source, destination]);

  return null;
}

export default function SafeRouteMap({
  routes,
  selectedRouteIndex,
  source,
  destination,
  userLocation,
}: SafeRouteMapProps) {
  const selectedRoute =
    routes.find(
      (route) =>
        route.route_index === selectedRouteIndex
    ) ?? null;

  return (
    <MapContainer
      center={[13.0827, 80.2707]}
      zoom={13}
      scrollWheelZoom={true}
      style={{
        height: "100%",
        width: "100%",
      }}
    >
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <MapController
        route={selectedRoute}
        source={source}
        destination={destination}
      />

      {routes.map((route, index) => {
        const positions = route.geometry.map(
          ([longitude, latitude]) =>
            [latitude, longitude] as [
              number,
              number
            ]
        );

        const isSelected =
          route.route_index === selectedRouteIndex;

        const color =
          ROUTE_COLORS[
            index % ROUTE_COLORS.length
          ];

        return (
          <Polyline
            key={route.route_index}
            positions={positions}
            pathOptions={{
              color,
              weight: isSelected ? 8 : 4,
              opacity: isSelected ? 1 : 0.35,
            }}
          />
        );
      })}

      {source && (
        <Marker
          position={[source.latitude, source.longitude]}
          icon={createSourceIcon()}
        >
          <Popup>
            <div style={{ padding: "4px 2px", fontFamily: "sans-serif" }}>
              <div style={{ color: "#059669", fontWeight: "bold", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                📍 Origin / Start Point
              </div>
              <div style={{ fontWeight: "600", fontSize: "13px", color: "#111827", marginTop: "2px" }}>
                {source.name}
              </div>
            </div>
          </Popup>
        </Marker>
      )}

      {destination && (
        <Marker
          position={[destination.latitude, destination.longitude]}
          icon={createDestIcon()}
        >
          <Popup>
            <div style={{ padding: "4px 2px", fontFamily: "sans-serif" }}>
              <div style={{ color: "#dc2626", fontWeight: "bold", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                🏁 Destination
              </div>
              <div style={{ fontWeight: "600", fontSize: "13px", color: "#111827", marginTop: "2px" }}>
                {destination.name}
              </div>
            </div>
          </Popup>
        </Marker>
      )}

      {userLocation && (
        <Marker
          position={userLocation}
          icon={createUserLocationIcon()}
        >
          <Popup>
            <div style={{ padding: "4px 2px", fontFamily: "sans-serif" }}>
              <div style={{ color: "#2563eb", fontWeight: "bold", fontSize: "12px" }}>
                📡 Live GPS Current Location
              </div>
            </div>
          </Popup>
        </Marker>
      )}
    </MapContainer>
  );
}