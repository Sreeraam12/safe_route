"use client";

import { useEffect, useState } from "react";
import { searchRoutes } from "../../services/routeApi";
import type { RouteSearchResponse } from "../../types/route";

interface SearchPanelProps {
  onRoutesFound: (data: RouteSearchResponse) => void;
  resetKey: number;
}

export default function SearchPanel({
  onRoutesFound,
  resetKey,
}: SearchPanelProps) {
  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setSource("");
    setDestination("");
    setError("");
  }, [resetKey]);
  const handleSearch = async () => {
    if (!source.trim() || !destination.trim()) {
      setError("Please enter both locations.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await searchRoutes(
        source.trim(),
        destination.trim()
      );

      onRoutesFound(result);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to find routes."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="absolute left-6 top-6 z-[1000] w-[360px] rounded-2xl bg-white p-5 shadow-xl">
      <h1 className="text-2xl font-bold text-gray-900">
        SafeRoute
      </h1>

      <p className="mt-1 text-sm text-gray-500">
        Find a safer route through Chennai
      </p>

      <div className="mt-5 space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            From
          </label>

          <input
            type="text"
            value={source}
            onChange={(event) => setSource(event.target.value)}
            placeholder="Enter starting point"
            className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-gray-500"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            To
          </label>

          <input
            type="text"
            value={destination}
            onChange={(event) =>
              setDestination(event.target.value)
            }
            placeholder="Enter destination"
            className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-gray-500"
          />
        </div>

        {error && (
          <p className="text-sm text-red-600">
            {error}
          </p>
        )}

        <button
          onClick={handleSearch}
          disabled={loading}
          className="w-full rounded-lg bg-black px-4 py-3 text-sm font-semibold text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Finding routes..." : "Find Safe Routes"}
        </button>
      </div>
    </div>
  );
}