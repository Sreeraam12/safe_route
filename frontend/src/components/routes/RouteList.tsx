"use client";

import type { RouteResult } from "../../types/route";

interface RouteListProps {
  routes: RouteResult[];
  selectedRouteIndex: number | null;
  onSelectRoute: (routeIndex: number) => void;
}

const ROUTE_COLORS = [
  "#16a34a",
  "#2563eb",
  "#9333ea",
  "#ea580c",
  "#dc2626",
];

export default function RouteList({
  routes,
  selectedRouteIndex,
  onSelectRoute,
}: RouteListProps) {
  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-lg font-bold text-gray-900">
          Safe Routes
        </h2>

        <p className="text-sm text-gray-500">
          {routes.length} route{routes.length !== 1 ? "s" : ""} found
        </p>
      </div>

      <div className="space-y-2">
        {routes.map((route, index) => {
          const isSelected =
            route.route_index === selectedRouteIndex;

          const color =
            ROUTE_COLORS[index % ROUTE_COLORS.length];

          return (
            <button
              key={route.route_index}
              onClick={() =>
                onSelectRoute(route.route_index)
              }
              className={`w-full rounded-xl border p-4 text-left transition ${
                isSelected
                  ? "border-gray-900 bg-gray-50 shadow-md"
                  : "border-gray-200 bg-white hover:border-gray-400"
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className="h-4 w-4 shrink-0 rounded-full"
                  style={{ backgroundColor: color }}
                />

                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-gray-900">
                      Route {route.rank}
                    </span>

                    <span className="text-sm font-semibold text-green-600">
                      {route.safety_score.toFixed(1)}
                    </span>
                  </div>

                  <div className="mt-1 flex gap-4 text-xs text-gray-500">
                    <span>
                      {route.distance_km.toFixed(2)} km
                    </span>

                    <span>
                      Risk {route.final_risk.toFixed(1)}
                    </span>

                    <span>
                      Traffic {route.traffic_risk.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}