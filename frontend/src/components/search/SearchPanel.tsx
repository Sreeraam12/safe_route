"use client";

import { useEffect, useState } from "react";
import { searchRoutes } from "../../services/routeApi";
import type { RouteSearchResponse } from "../../types/route";

interface SearchPanelProps {
  onRoutesFound: (data: RouteSearchResponse) => void;
  resetKey: number;
}

const CHENNAI_QUICK_ROUTES = [
  { from: "Chennai Central", to: "Marina Beach", label: "Central ➔ Marina" },
  { from: "T Nagar", to: "Adyar", label: "T Nagar ➔ Adyar" },
  { from: "Guindy", to: "Velachery", label: "Guindy ➔ Velachery" },
];

export default function SearchPanel({
  onRoutesFound,
  resetKey,
}: SearchPanelProps) {
  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [travelDate, setTravelDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [travelTime, setTravelTime] = useState(() => {
    const d = new Date();
    return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setSource("");
    setDestination("");
    setError("");
  }, [resetKey]);

  const handleSearch = async () => {
    if (!source.trim() || !destination.trim()) {
      setError("Please enter both starting point and destination.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await searchRoutes(
        source.trim(),
        destination.trim(),
        travelDate,
        travelTime
      );

      onRoutesFound(result);
    } catch (err: any) {
      setError(
        err instanceof Error ? err.message : "Failed to find routes."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleQuickSelect = (from: string, to: string) => {
    setSource(from);
    setDestination(to);
    setError("");
  };

  const handleSwap = () => {
    const temp = source;
    setSource(destination);
    setDestination(temp);
  };

  return (
    <div className="absolute left-6 top-6 z-[1000] w-[370px] rounded-3xl bg-white/95 p-5 shadow-2xl backdrop-blur-xl border border-gray-100">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-md shadow-emerald-600/20">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-5 h-5 text-white"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <path d="m9 12 2 2 4-4" />
          </svg>
        </div>
        <div>
          <h1 className="text-xl font-extrabold text-gray-900 tracking-tight">SafeRoute</h1>
          <p className="text-[11px] font-medium text-emerald-700">
            Time-Aware Women's Safety Routing • Chennai
          </p>
        </div>
      </div>

      {/* Quick Corridors */}
      <div className="mt-3.5 flex flex-wrap gap-1.5">
        {CHENNAI_QUICK_ROUTES.map((item, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleQuickSelect(item.from, item.to)}
            className="rounded-lg bg-gray-50 border border-gray-200/70 px-2 py-1 text-[11px] font-semibold text-gray-600 hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-200 transition"
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="mt-4 space-y-3.5">
        <div>
          <label className="mb-1 flex items-center justify-between text-xs font-semibold text-gray-700">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-emerald-500 inline-block"></span>
              Origin / Starting Point
            </span>
            {source && (
              <button
                type="button"
                onClick={() => setSource("")}
                className="text-[10px] text-gray-400 hover:text-gray-600"
              >
                Clear
              </button>
            )}
          </label>

          <input
            type="text"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="e.g. Chennai Central or T Nagar"
            className="w-full rounded-xl border border-gray-200 bg-gray-50/50 px-3.5 py-2.5 text-xs text-gray-900 outline-none focus:border-emerald-500 focus:bg-white focus:ring-1 focus:ring-emerald-500 transition"
          />
        </div>

        <div className="relative">
          <div className="absolute -top-3 right-3 z-10">
            <button
              type="button"
              onClick={handleSwap}
              title="Swap start and destination"
              className="flex h-6 w-6 items-center justify-center rounded-full bg-white border border-gray-200 shadow-sm text-gray-500 hover:text-emerald-600 hover:border-emerald-300 transition"
            >
              ⇅
            </button>
          </div>

          <label className="mb-1 flex items-center justify-between text-xs font-semibold text-gray-700">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-red-500 inline-block"></span>
              Destination
            </span>
            {destination && (
              <button
                type="button"
                onClick={() => setDestination("")}
                className="text-[10px] text-gray-400 hover:text-gray-600"
              >
                Clear
              </button>
            )}
          </label>

          <input
            type="text"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="e.g. Marina Beach or Adyar"
            className="w-full rounded-xl border border-gray-200 bg-gray-50/50 px-3.5 py-2.5 text-xs text-gray-900 outline-none focus:border-emerald-500 focus:bg-white focus:ring-1 focus:ring-emerald-500 transition"
          />
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-gray-600">
              📅 Travel Date
            </label>
            <input
              type="date"
              value={travelDate}
              onChange={(e) => setTravelDate(e.target.value)}
              className="w-full rounded-xl border border-gray-200 bg-gray-50/50 px-2.5 py-2 text-xs outline-none focus:border-emerald-500 focus:bg-white transition"
            />
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-gray-600">
              ⏰ Departure Time
            </label>
            <input
              type="time"
              value={travelTime}
              onChange={(e) => setTravelTime(e.target.value)}
              className="w-full rounded-xl border border-gray-200 bg-gray-50/50 px-2.5 py-2 text-xs outline-none focus:border-emerald-500 focus:bg-white transition"
            />
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-2.5 text-xs text-red-600 font-medium">
            {error}
          </div>
        )}

        <button
          onClick={handleSearch}
          disabled={loading}
          className="w-full rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-3 text-xs font-bold text-white shadow-lg shadow-emerald-600/25 transition hover:from-emerald-500 hover:to-teal-500 disabled:cursor-not-allowed disabled:opacity-60 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="h-4 w-4 animate-spin text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              <span>Analyzing Chennai Roads...</span>
            </>
          ) : (
            <>
              <span>🔍</span>
              <span>Find Safe Routes</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}