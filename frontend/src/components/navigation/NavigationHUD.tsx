"use client";

import { useEffect, useState, useRef } from "react";
import type { RouteResult, NavigationStatus } from "../../types/route";
import { updateGPSLocation, endNavigation } from "../../services/routeApi";

interface NavigationHUDProps {
  tripId: string;
  route: RouteResult;
  onEndTrip: () => void;
  onRouteUpdated: (newRoute: RouteResult) => void;
  onUserLocationUpdate: (coords: [number, number]) => void;
}

export default function NavigationHUD({
  tripId,
  route,
  onEndTrip,
  onRouteUpdated,
  onUserLocationUpdate,
}: NavigationHUDProps) {
  const [navStatus, setNavStatus] = useState<NavigationStatus | null>(null);
  const [simulating, setSimulating] = useState(false);
  const [simStepIndex, setSimStepIndex] = useState(0);
  const [isOffRouteAlert, setIsOffRouteAlert] = useState(false);
  const [isReroutingAlert, setIsReroutingAlert] = useState(false);

  const routeGeometry = route.geometry;
  const simIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initial status
  useEffect(() => {
    if (routeGeometry.length > 0) {
      const [lon, lat] = routeGeometry[0];
      onUserLocationUpdate([lat, lon]);
      sendGPS(lat, lon, 25.0);
    }
    return () => {
      if (simIntervalRef.current) clearInterval(simIntervalRef.current);
    };
  }, []);

  const sendGPS = async (lat: number, lon: number, speed: number = 25.0) => {
    try {
      const status = await updateGPSLocation({
        trip_id: tripId,
        latitude: lat,
        longitude: lon,
        speed,
      });

      setNavStatus(status);
      setIsOffRouteAlert(status.off_route);
      setIsReroutingAlert(status.rerouting);

      if (status.new_route) {
        onRouteUpdated(status.new_route);
      }
    } catch (err) {
      console.error("GPS update error:", err);
    }
  };

  // Start / stop simulation along the route
  const toggleSimulation = () => {
    if (simulating) {
      if (simIntervalRef.current) clearInterval(simIntervalRef.current);
      setSimulating(false);
    } else {
      setSimulating(true);
      let idx = simStepIndex;

      simIntervalRef.current = setInterval(() => {
        idx += 1;
        if (idx >= routeGeometry.length) {
          if (simIntervalRef.current) clearInterval(simIntervalRef.current);
          setSimulating(false);
          return;
        }

        setSimStepIndex(idx);
        const [lon, lat] = routeGeometry[idx];
        onUserLocationUpdate([lat, lon]);
        sendGPS(lat, lon, 30.0);
      }, 2500);
    }
  };

  // Simulate deliberate off-route deviation to trigger automatic re-routing
  const triggerOffRouteDeviation = () => {
    if (routeGeometry.length > 0) {
      // Offset by ~250m west to be distinctly off-route
      const [lon, lat] = routeGeometry[Math.min(simStepIndex + 2, routeGeometry.length - 1)];
      const offLat = lat + 0.003;
      const offLon = lon - 0.003;
      onUserLocationUpdate([offLat, offLon]);
      sendGPS(offLat, offLon, 20.0);
    }
  };

  const handleEndTrip = async () => {
    if (simIntervalRef.current) clearInterval(simIntervalRef.current);
    try {
      await endNavigation(tripId);
    } catch {
      // ignore
    }
    onEndTrip();
  };

  return (
    <div className="absolute left-5 right-5 top-5 z-[1000] mx-auto max-w-lg space-y-3">
      {/* Off-Route / Re-routing Warning Alert */}
      {isReroutingAlert && (
        <div className="flex items-center gap-2 rounded-xl bg-amber-500 p-3 text-xs font-semibold text-white shadow-lg animate-pulse">
          <span>🔄</span>
          <span>Off-route detected. Automatically calculating new safe route from current position...</span>
        </div>
      )}

      {/* Main Navigation Heads-Up Display */}
      <div className="rounded-2xl bg-white/95 p-4 shadow-2xl backdrop-blur border border-gray-100">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-xl font-bold text-white shadow-md">
            🧭
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide">
              {navStatus?.distance_to_turn_formatted ? `In ${navStatus.distance_to_turn_formatted}` : "Next Direction"}
            </p>
            <h2 className="mt-0.5 text-lg font-bold text-gray-900 leading-tight">
              {navStatus?.current_instruction || route.instructions[0]?.instruction || "Follow route"}
            </h2>
            {navStatus?.next_instruction && (
              <p className="mt-1 text-xs text-gray-400">
                Then: {navStatus.next_instruction}
              </p>
            )}
          </div>
        </div>

        {/* Real-time Metrics Bar */}
        <div className="mt-4 grid grid-cols-3 gap-2 border-t border-gray-100 pt-3 text-center">
          <div>
            <p className="text-[10px] text-gray-400 uppercase">Remaining</p>
            <p className="text-sm font-bold text-gray-800">
              {navStatus?.remaining_distance_km ?? route.distance_km} km
            </p>
          </div>
          <div>
            <p className="text-[10px] text-gray-400 uppercase">Est. Time</p>
            <p className="text-sm font-bold text-gray-800">
              {navStatus?.eta_minutes ?? Math.round((route.distance_km / 25) * 60)} min
            </p>
          </div>
          <div>
            <p className="text-[10px] text-gray-400 uppercase">Speed</p>
            <p className="text-sm font-bold text-gray-800">
              {simulating ? "30 km/h" : "Live GPS"}
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="mt-4 flex gap-2">
          <button
            onClick={toggleSimulation}
            className={`flex-1 rounded-xl py-2.5 text-xs font-semibold transition ${
              simulating
                ? "bg-amber-100 text-amber-800 hover:bg-amber-200"
                : "bg-gray-100 text-gray-800 hover:bg-gray-200"
            }`}
          >
            {simulating ? "⏸ Pause Movement" : "▶ Simulate GPS Drive"}
          </button>

          <button
            onClick={triggerOffRouteDeviation}
            title="Simulates vehicle driving off-course to verify dynamic re-routing"
            className="rounded-xl border border-gray-200 px-3 py-2.5 text-xs font-semibold text-gray-600 hover:bg-gray-50"
          >
            Simulate Deviation
          </button>

          <button
            onClick={handleEndTrip}
            className="rounded-xl bg-red-600 px-4 py-2.5 text-xs font-semibold text-white shadow transition hover:bg-red-700"
          >
            End Trip
          </button>
        </div>
      </div>
    </div>
  );
}

