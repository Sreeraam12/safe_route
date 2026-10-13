"use client";

import type { RouteResult } from "../../types/route";

interface RouteDetailsProps {
  route: RouteResult | null;
  onStartNavigation?: (route: RouteResult) => void;
}

export default function RouteDetails({
  route,
  onStartNavigation,
}: RouteDetailsProps) {
  if (!route) {
    return null;
  }

  const effectiveSafety = route.personalized_safety_score !== undefined
    ? route.personalized_safety_score
    : route.safety_score;

  const safety = Math.round(effectiveSafety);

  let safetyLabel = "Needs caution";
  if (safety >= 75) {
    safetyLabel = "Very safe";
  } else if (safety >= 60) {
    safetyLabel = "Relatively safe";
  }

  const formatPeriod = (period?: string) => {
    switch (period) {
      case "morning": return "Morning (high daylight)";
      case "afternoon": return "Afternoon";
      case "evening": return "Evening (dusk / transition)";
      case "night": return "Night (caution)";
      case "late_night": return "Late Night (high vulnerability)";
      default: return "Normal";
    }
  };

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

        {/* Time Period Context Badge */}
        {route.time_period && (
          <div className="mt-2 flex items-center gap-2">
            <span className="inline-flex items-center rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800 ring-1 ring-inset ring-amber-600/20">
              🕒 {formatPeriod(route.time_period)}
            </span>
            {route.personal_adjustment !== undefined && route.personal_adjustment !== 0 && (
              <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${
                route.personal_adjustment > 0
                  ? "bg-purple-50 text-purple-700 ring-1 ring-purple-600/20"
                  : "bg-blue-50 text-blue-700 ring-1 ring-blue-600/20"
              }`}>
                Twin Adj: {route.personal_adjustment > 0 ? `+${route.personal_adjustment}` : route.personal_adjustment}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Safety score */}
      <div className="mb-4 rounded-xl bg-green-50 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-gray-500">
              {route.personalized_safety_score !== undefined ? "Personalized Safety Score" : "Global Safety Score"}
            </p>

            <p className="mt-1 text-3xl font-bold text-green-600">
              {effectiveSafety.toFixed(1)}
            </p>

            {route.personalized_safety_score !== undefined && (
              <p className="mt-0.5 text-xs text-gray-400">
                Global Base: {route.safety_score.toFixed(1)}
              </p>
            )}
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
                strokeDasharray={`${effectiveSafety}, 100`}
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
              width: `${effectiveSafety}%`,
            }}
          />
        </div>
      </div>

      {/* Personal Segment Memory Intelligence Badges */}
      {Boolean(
        (route.familiar_segments_count && route.familiar_segments_count > 0) ||
        (route.avoided_segments_count && route.avoided_segments_count > 0) ||
        (route.segment_memory_adjustment && Math.abs(route.segment_memory_adjustment) > 0.05)
      ) && (
        <div className="mb-4 rounded-xl bg-slate-50 border border-slate-200 p-3 text-xs">
          <div className="flex items-center justify-between font-bold text-slate-800 mb-1.5">
            <span className="flex items-center gap-1.5">
              <span>🧠</span> Road Memory Intelligence
            </span>
            {route.segment_memory_adjustment !== undefined && Math.abs(route.segment_memory_adjustment) > 0.05 && (
              <span className={`px-2 py-0.5 rounded-full font-extrabold text-[10px] ${
                route.segment_memory_adjustment < 0
                  ? "bg-emerald-100 text-emerald-800"
                  : "bg-amber-100 text-amber-800"
              }`}>
                {route.segment_memory_adjustment < 0
                  ? `${route.segment_memory_adjustment.toFixed(1)} Familiarity Bonus`
                  : `+${route.segment_memory_adjustment.toFixed(1)} Avoidance Risk`}
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {Boolean(route.familiar_segments_count && route.familiar_segments_count > 0) && (
              <span className="inline-flex items-center gap-1 rounded-lg bg-emerald-50 px-2 py-1 text-[11px] font-semibold text-emerald-700 border border-emerald-200">
                <span>⭐</span> Familiar corridor ({route.familiar_segments_count} roads)
              </span>
            )}
            {Boolean(route.avoided_segments_count && route.avoided_segments_count > 0) && (
              <span className="inline-flex items-center gap-1 rounded-lg bg-amber-50 px-2 py-1 text-[11px] font-semibold text-amber-700 border border-amber-200">
                <span>⚠️</span> Contains avoided corridor ({route.avoided_segments_count})
              </span>
            )}
          </div>
        </div>
      )}

      {/* Start Live Navigation Action Button */}
      {onStartNavigation && (
        <button
          onClick={() => onStartNavigation(route)}
          className="mb-4 flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white shadow-md transition hover:bg-blue-700 active:scale-[0.98]"
        >
          <span>🧭</span>
          <span>Start Live GPS Navigation</span>
        </button>
      )}

      {/* Route statistics */}
      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-lg bg-gray-50 p-2.5 text-center">
          <p className="text-[11px] text-gray-500">Distance</p>
          <p className="mt-0.5 text-sm font-bold text-gray-900">
            {route.distance_km.toFixed(2)} km
          </p>
        </div>

        <div className="rounded-lg bg-gray-50 p-2.5 text-center">
          <p className="text-[11px] text-gray-500">Risk</p>
          <p className="mt-0.5 text-sm font-bold text-gray-900">
            {(route.personalized_risk ?? route.final_risk).toFixed(1)}
          </p>
        </div>

        <div className="rounded-lg bg-gray-50 p-2.5 text-center">
          <p className="text-[11px] text-gray-500">Live Traffic</p>
          <p className="mt-0.5 text-sm font-bold text-gray-900">
            {route.traffic_risk.toFixed(1)}
          </p>
        </div>
      </div>

      {/* Turn-by-turn Preview */}
      <div className="mt-5">
        <h3 className="mb-2.5 text-xs font-bold uppercase tracking-wide text-gray-500">
          Route Itinerary ({route.instructions.length} steps)
        </h3>

        <div className="max-h-48 space-y-2 overflow-y-auto pr-1">
          {route.instructions.map((instruction) => (
            <div
              key={instruction.step}
              className="flex gap-2.5 text-xs"
            >
              <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-gray-200 text-[10px] font-semibold text-gray-700">
                {instruction.step}
              </div>

              <div className="min-w-0 flex-1">
                <p className="text-gray-800">
                  {instruction.instruction}
                </p>
                {instruction.distance && (
                  <p className="text-[10px] text-gray-400">
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