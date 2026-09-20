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
}

const ROUTE_COLORS = [
  "#16a34a",
  "#2563eb",
  "#9333ea",
  "#ea580c",
  "#dc2626",
];

function MapController({
  route,
}: {
  route: RouteResult | null;
}) {
  const map = useMap();

  useEffect(() => {
    if (!route || route.geometry.length === 0) {
      return;
    }

    const positions = route.geometry.map(
      ([longitude, latitude]) =>
        [latitude, longitude] as [number, number]
    );

    map.fitBounds(positions, {
      padding: [60, 60],
      maxZoom: 15,
    });
  }, [map, route]);

  return null;
}

export default function SafeRouteMap({
  routes,
  selectedRouteIndex,
  source,
  destination,
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

      <MapController route={selectedRoute} />

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
          position={[
            source.latitude,
            source.longitude,
          ]}
        >
          <Popup>
            <strong>Start</strong>
            <br />
            {source.name}
          </Popup>
        </Marker>
      )}

      {destination && (
        <Marker
          position={[
            destination.latitude,
            destination.longitude,
          ]}
        >
          <Popup>
            <strong>Destination</strong>
            <br />
            {destination.name}
          </Popup>
        </Marker>
      )}
    </MapContainer>
  );
}