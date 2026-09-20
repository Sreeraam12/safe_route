"use client";

import type { RouteResult } from "../../types/route";

interface RouteDetailsProps {
  route: RouteResult | null;
}

export default function RouteDetails({
  route,
}: RouteDetailsProps) {
  if (!route) {
    return null;
  }

  const safety = Math.round(route.safety_score);

  let safetyLabel = "Needs caution";

  if (safety >= 75) {
    safetyLabel = "Very safe";
  } else if (safety >= 60) {
    safetyLabel = "Relatively safe";
  }

  return (
    <div>
      {/* Selected route header */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
              Selected Route
            </p>

            <h2 className="mt-1 text-xl font-bold text-gray-900">
              Route {route.rank}
            </h2>
          </div>

          <div className="rounded-full bg-green-50 px-3 py-1">
            <span className="text-sm font-semibold text-green-600">
              {safetyLabel}
            </span>
          </div>
        </div>
      </div>

      {/* Safety score */}
      <div className="mb-4 rounded-xl bg-green-50 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">
              Safety Score
            </p>

            <p className="mt-1 text-3xl font-bold text-green-600">
              {route.safety_score.toFixed(1)}
            </p>
          </div>

          <div className="relative h-16 w-16">
            <svg
              className="h-16 w-16 -rotate-90"
              viewBox="0 0 36 36"
            >
              <path
                d="M18 2.0845
                   a 15.9155 15.9155 0 0 1 0 31.831
                   a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#dcfce7"
                strokeWidth="3"
              />

              <path
                d="M18 2.0845
                   a 15.9155 15.9155 0 0 1 0 31.831
                   a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#16a34a"
                strokeWidth="3"
                strokeDasharray={`${route.safety_score}, 100`}
                strokeLinecap="round"
              />
            </svg>

            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-xs font-bold text-green-700">
                {safety}
              </span>
            </div>
          </div>
        </div>

        <div className="mt-3 h-2 overflow-hidden rounded-full bg-green-100">
          <div
            className="h-full rounded-full bg-green-500 transition-all"
            style={{
              width: `${route.safety_score}%`,
            }}
          />
        </div>
      </div>

      {/* Route statistics */}
      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-lg bg-gray-50 p-3">
          <p className="text-xs text-gray-500">
            Distance
          </p>

          <p className="mt-1 font-bold text-gray-900">
            {route.distance_km.toFixed(2)} km
          </p>
        </div>

        <div className="rounded-lg bg-gray-50 p-3">
          <p className="text-xs text-gray-500">
            Risk
          </p>

          <p className="mt-1 font-bold text-gray-900">
            {route.final_risk.toFixed(1)}
          </p>
        </div>

        <div className="rounded-lg bg-gray-50 p-3">
          <p className="text-xs text-gray-500">
            Traffic
          </p>

          <p className="mt-1 font-bold text-gray-900">
            {route.traffic_risk.toFixed(1)}
          </p>
        </div>
      </div>

      {/* Turn-by-turn */}
      <div className="mt-6">
        <h3 className="mb-3 font-semibold text-gray-900">
          Turn-by-turn
        </h3>

        <div className="space-y-3">
          {route.instructions.map((instruction) => (
            <div
              key={instruction.step}
              className="flex gap-3"
            >
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-900 text-xs font-semibold text-white">
                {instruction.step}
              </div>

              <div className="min-w-0">
                <p className="text-sm text-gray-800">
                  {instruction.instruction}
                </p>

                {instruction.distance && (
                  <p className="mt-1 text-xs text-gray-400">
                    {instruction.distance}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}