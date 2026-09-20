"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

import SearchPanel from "../components/search/SearchPanel";
import RouteList from "../components/routes/RouteList";
import RouteDetails from "../components/routes/RouteDetails";
import type { RouteSearchResponse } from "../types/route";

const SafeRouteMap = dynamic(
  () => import("../components/map/SafeRouteMap"),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full w-full items-center justify-center bg-gray-100">
        Loading map...
      </div>
    ),
  }
);

export default function Home() {
  const [routeData, setRouteData] =
    useState<RouteSearchResponse | null>(null);

  const [selectedRouteIndex, setSelectedRouteIndex] =
    useState<number | null>(null);

  const [showResults, setShowResults] =
    useState(false);
  
  const [searchResetKey, setSearchResetKey] =
    useState(0);

  const selectedRoute =
    routeData?.routes.find(
      (route) =>
        route.route_index === selectedRouteIndex
    ) ?? null;

  const handleRoutesFound = (
    data: RouteSearchResponse
  ) => {
    setRouteData(data);

    if (data.routes.length > 0) {
      setSelectedRouteIndex(
        data.routes[0].route_index
      );
    } else {
      setSelectedRouteIndex(null);
    }

    setShowResults(true);
  };

  const handleNewSearch = () => {
    setShowResults(false);
    setRouteData(null);
    setSelectedRouteIndex(null);
    setSearchResetKey((value) => value + 1);
  };

  return (
    <main className="relative h-screen w-screen overflow-hidden">

      {/* Map */}
      <SafeRouteMap
        routes={routeData?.routes ?? []}
        selectedRouteIndex={selectedRouteIndex}
        source={routeData?.source ?? null}
        destination={routeData?.destination ?? null}
      />

      {/* Search Panel */}
      {!showResults && (
        <SearchPanel
          onRoutesFound={handleRoutesFound}
          resetKey={searchResetKey}
        />
      )}

      {/* Results Panel */}
      {showResults &&
        routeData &&
        routeData.routes.length > 0 && (
          <aside className="absolute bottom-5 left-5 top-5 z-[1000] w-[380px] overflow-y-auto rounded-2xl bg-white/95 p-4 shadow-2xl backdrop-blur">

            {/* Header */}
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  SafeRoute
                </h1>

                <p className="text-sm text-gray-500">
                  Route alternatives
                </p>
              </div>

              <button
                onClick={handleNewSearch}
                className="flex h-9 w-9 items-center justify-center rounded-full text-2xl text-gray-500 transition hover:bg-gray-100 hover:text-gray-900"
                title="New search"
              >
                ×
              </button>
            </div>

            {/* Selected Route Details */}
            <RouteDetails
              route={selectedRoute}
            />

            <div className="my-5 border-t border-gray-200" />

            {/* Route List */}
            <RouteList
              routes={routeData.routes}
              selectedRouteIndex={selectedRouteIndex}
              onSelectRoute={setSelectedRouteIndex}
            />

          </aside>
        )}
    </main>
  );
}