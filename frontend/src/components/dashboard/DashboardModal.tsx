"use client";

import { useState, useEffect } from "react";
import { getTripHistory, getTwinState } from "../../services/routeApi";
import type { TripHistoryItem, PersonalTwinState } from "../../types/route";

interface DashboardModalProps {
  onClose: () => void;
}

export default function DashboardModal({ onClose }: DashboardModalProps) {
  const [activeTab, setActiveTab] = useState<"history" | "twin">("history");
  const [trips, setTrips] = useState<TripHistoryItem[]>([]);
  const [twin, setTwin] = useState<PersonalTwinState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [historyData, twinData] = await Promise.allSettled([
          getTripHistory(),
          getTwinState(),
        ]);

        if (historyData.status === "fulfilled") {
          setTrips(historyData.value);
        }
        if (twinData.status === "fulfilled") {
          setTwin(twinData.value);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Compute summary stats
  const totalTrips = trips.length;
  const completedTrips = trips.filter((t) => t.completed).length;
  const avgSafetyScore =
    totalTrips > 0
      ? Math.round(
          trips.reduce((acc, t) => acc + (t.selected_safety_score || 0), 0) /
            totalTrips
        )
      : null;
  const totalDistanceKm = trips
    .reduce((acc, t) => acc + (t.selected_distance_km || 0), 0)
    .toFixed(1);

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="flex h-[90vh] max-h-[750px] w-full max-w-4xl flex-col rounded-3xl bg-white shadow-2xl overflow-hidden border border-gray-100">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4 bg-gray-50/70">
          <div>
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <span>📊</span> SafeRoute Dashboard
            </h2>
            <p className="text-xs text-gray-500">
              Chennai Women's Safe Mobility & Personal Digital Twin Analytics
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-gray-400 hover:bg-gray-200 hover:text-gray-700 transition"
          >
            ✕
          </button>
        </div>

        {/* Quick Stats Banner */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 border-b border-gray-100 bg-gray-50/40 p-4">
          <div className="rounded-2xl bg-white p-3 border border-gray-100 shadow-sm">
            <span className="text-xs font-medium text-gray-400">Total Trips</span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-gray-900">{totalTrips}</span>
              <span className="text-xs text-emerald-600 font-medium">({completedTrips} done)</span>
            </div>
          </div>

          <div className="rounded-2xl bg-white p-3 border border-gray-100 shadow-sm">
            <span className="text-xs font-medium text-gray-400">Avg Safety Score</span>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-2xl font-bold text-emerald-600">
                {avgSafetyScore !== null ? `${avgSafetyScore}/100` : "N/A"}
              </span>
            </div>
          </div>

          <div className="rounded-2xl bg-white p-3 border border-gray-100 shadow-sm">
            <span className="text-xs font-medium text-gray-400">Total Distance</span>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-2xl font-bold text-blue-600">{totalDistanceKm}</span>
              <span className="text-xs text-gray-500">km</span>
            </div>
          </div>

          <div className="rounded-2xl bg-white p-3 border border-gray-100 shadow-sm">
            <span className="text-xs font-medium text-gray-400">Twin Confidence</span>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-2xl font-bold text-purple-600">
                {twin ? `${Math.round(twin.model_confidence * 100)}%` : "N/A"}
              </span>
              <span className="text-[10px] text-gray-400">
                {twin && twin.model_confidence > 0.6 ? "Adaptive" : "Calibrating"}
              </span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-gray-200 px-6 bg-white">
          <button
            onClick={() => setActiveTab("history")}
            className={`py-3 px-4 text-sm font-semibold border-b-2 transition ${
              activeTab === "history"
                ? "border-emerald-600 text-emerald-600"
                : "border-transparent text-gray-500 hover:text-gray-800"
            }`}
          >
            📜 Trip History ({trips.length})
          </button>
          <button
            onClick={() => setActiveTab("twin")}
            className={`py-3 px-4 text-sm font-semibold border-b-2 transition ${
              activeTab === "twin"
                ? "border-purple-600 text-purple-600"
                : "border-transparent text-gray-500 hover:text-gray-800"
            }`}
          >
            🧬 Digital Twin State
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50/30">
          {loading ? (
            <div className="flex h-48 items-center justify-center text-sm text-gray-400">
              Loading dashboard data...
            </div>
          ) : error ? (
            <div className="rounded-xl bg-red-50 p-4 text-sm text-red-600 border border-red-100">
              {error}
            </div>
          ) : activeTab === "history" ? (
            <div>
              {trips.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="h-16 w-16 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center text-2xl mb-3">
                    🗺️
                  </div>
                  <h3 className="text-base font-semibold text-gray-800">No Trips Logged Yet</h3>
                  <p className="mt-1 text-xs text-gray-500 max-w-sm">
                    Search for routes across Chennai, start live GPS navigation, and complete your trips to build your safety log and train your Digital Twin!
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {trips.map((trip) => {
                    const isHighSafety = trip.selected_safety_score >= 70;
                    const isMedSafety = trip.selected_safety_score >= 50 && trip.selected_safety_score < 70;

                    return (
                      <div
                        key={trip.id}
                        className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm hover:shadow-md transition"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-gray-900 text-sm">
                                {trip.source_zone} → {trip.destination_zone}
                              </span>
                              <span
                                className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                                  trip.completed
                                    ? "bg-emerald-100 text-emerald-700"
                                    : "bg-amber-100 text-amber-700"
                                }`}
                              >
                                {trip.completed ? "Completed" : "In Progress"}
                              </span>
                            </div>
                            <p className="mt-0.5 text-xs text-gray-400">
                              📅 {trip.travel_date} at {trip.travel_time} • {trip.travel_mode.toUpperCase()}
                            </p>
                          </div>

                          <div className="text-right">
                            <span
                              className={`inline-block rounded-xl px-2.5 py-1 text-xs font-bold ${
                                isHighSafety
                                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                  : isMedSafety
                                  ? "bg-amber-50 text-amber-700 border border-amber-200"
                                  : "bg-red-50 text-red-700 border border-red-200"
                              }`}
                            >
                              Safety {trip.selected_safety_score}
                            </span>
                            <p className="mt-1 text-xs text-gray-500 font-medium">
                              {trip.selected_distance_km} km
                            </p>
                          </div>
                        </div>

                        {/* Feedback Details if submitted */}
                        {trip.feedback && (
                          <div className="mt-3 rounded-xl bg-gray-50 p-3 border border-gray-100 text-xs">
                            <div className="flex items-center justify-between text-gray-600 font-medium mb-1">
                              <span>User Trip Feedback</span>
                              <span className="text-amber-500">
                                {"★".repeat(trip.feedback.safety_rating)}
                                {"☆".repeat(5 - trip.feedback.safety_rating)}
                              </span>
                            </div>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] text-gray-600 mt-2 bg-white/70 p-2 rounded-lg border border-gray-100">
                              <div>Comfort: <span className="font-semibold text-gray-800">{trip.feedback.comfort_rating != null ? `${trip.feedback.comfort_rating}/5` : "N/A"}</span></div>
                              <div>Lighting: <span className="font-semibold text-gray-800">{trip.feedback.lighting_rating != null ? `${trip.feedback.lighting_rating}/5` : "N/A"}</span></div>
                              <div>Crowd: <span className="font-semibold text-gray-800">{trip.feedback.crowd_rating != null ? `${trip.feedback.crowd_rating}/5` : "N/A"}</span></div>
                              <div>Navigation: <span className="font-semibold text-gray-800">{trip.feedback.navigation_rating != null ? `${trip.feedback.navigation_rating}/5` : "N/A"}</span></div>
                            </div>
                            {trip.feedback.feedback_text && (
                              <p className="mt-2 text-gray-700 italic border-t border-gray-200/60 pt-1.5">
                                "{trip.feedback.feedback_text}"
                              </p>
                            )}
                            {trip.feedback.felt_unsafe && (
                              <div className="mt-2 text-[11px] font-semibold text-rose-600 flex items-center gap-1">
                                ⚠️ Marked feeling unsafe along this corridor.
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ) : (
            /* Twin State Tab */
            twin && (
              <div className="space-y-6">
                <div className="rounded-2xl bg-purple-50/60 border border-purple-100 p-5">
                  <h3 className="text-sm font-bold text-purple-900 flex items-center gap-2">
                    <span>🧬</span> Active Twin Representation
                  </h3>
                  <p className="mt-1 text-xs text-purple-700">
                    Your Personal Digital Twin maintains adaptive risk sensitivity parameters that continuously calibrate with every trip decision and post-trip feedback in Chennai.
                  </p>
                  <div className="mt-3 flex items-center gap-3">
                    <span className="text-xs font-semibold text-purple-800">
                      Model Adaptive Weight:
                    </span>
                    <div className="flex-1 max-w-xs h-2 rounded-full bg-purple-200 overflow-hidden">
                      <div
                        className="h-full bg-purple-600 transition-all duration-500"
                        style={{ width: `${Math.round(twin.model_confidence * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs font-bold text-purple-900">
                      {Math.round(twin.model_confidence * 100)}%
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { label: "💡 Lighting Preference Weight", val: twin.lighting_weight, desc: "Favors well-lit avenues and street-lamp density" },
                    { label: "🛡️ Crime Sensitivity Weight", val: twin.crime_weight, desc: "Avoidance penalty against historical incident corridors" },
                    { label: "👥 Crowd & Footfall Priority", val: twin.crowd_weight, desc: "Preference for active shops and pedestrian presence" },
                    { label: "🚧 Isolation Aversion Weight", val: twin.isolation_weight, desc: "Penalizes desolate or blind road segments" },
                    { label: "🌙 Night-time Vigilance Weight", val: twin.night_weight, desc: "Heightens nighttime risk mitigation factors" },
                    { label: "↔️ Detour Tolerance", val: twin.detour_tolerance, desc: "Willingness to take longer routes for enhanced safety" },
                  ].map((item, idx) => (
                    <div
                      key={idx}
                      className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm"
                    >
                      <div className="flex items-center justify-between text-xs font-semibold text-gray-800">
                        <span>{item.label}</span>
                        <span className="font-mono text-purple-700 font-bold">
                          {(item.val * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="mt-1 text-[11px] text-gray-400">{item.desc}</p>
                      <div className="mt-3 h-2 w-full rounded-full bg-gray-100 overflow-hidden">
                        <div
                          className="h-full bg-purple-500 rounded-full"
                          style={{ width: `${Math.min(100, Math.max(0, item.val * 100))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}

