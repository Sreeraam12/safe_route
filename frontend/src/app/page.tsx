"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";

import SearchPanel from "../components/search/SearchPanel";
import RouteList from "../components/routes/RouteList";
import RouteDetails from "../components/routes/RouteDetails";
import NavigationHUD from "../components/navigation/NavigationHUD";
import LoginPage, { SafeRouteLogo } from "../components/auth/LoginPage";
import PreferencesModal from "../components/preferences/PreferencesModal";
import TripFeedbackModal from "../components/feedback/TripFeedbackModal";
import DashboardModal from "../components/dashboard/DashboardModal";
import EmergencyModal from "../components/emergency/EmergencyModal";

import type { RouteSearchResponse, RouteResult, UserProfile } from "../types/route";
import { getMe, createTrip, startNavigation } from "../services/routeApi";

const SafeRouteMap = dynamic(
  () => import("../components/map/SafeRouteMap"),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full w-full items-center justify-center bg-slate-900 text-slate-300">
        <div className="flex flex-col items-center gap-2">
          <SafeRouteLogo className="w-10 h-10 animate-pulse" />
          <span className="text-xs font-semibold">Loading Chennai Map Network...</span>
        </div>
      </div>
    ),
  }
);

export default function Home() {
  const [routeData, setRouteData] = useState<RouteSearchResponse | null>(null);
  const [selectedRouteIndex, setSelectedRouteIndex] = useState<number | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [searchResetKey, setSearchResetKey] = useState(0);

  // Authentication State
  const [user, setUser] = useState<UserProfile | null>(null);
  const [authChecking, setAuthChecking] = useState(true);

  // Modals
  const [showPreferencesModal, setShowPreferencesModal] = useState(false);
  const [showDashboardModal, setShowDashboardModal] = useState(false);
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);

  // Live Navigation State
  const [isNavigating, setIsNavigating] = useState(false);
  const [activeTripId, setActiveTripId] = useState<string | null>(null);
  const [userLiveCoords, setUserLiveCoords] = useState<[number, number] | null>(null);

  // Post-trip feedback
  const [completedTripId, setCompletedTripId] = useState<string | null>(null);

  useEffect(() => {
    async function checkAuth() {
      try {
        const token =
          typeof window !== "undefined"
            ? localStorage.getItem("saferoute_token")
            : null;
        if (token) {
          const u = await getMe();
          setUser(u);
        } else {
          setUser(null);
        }
      } catch {
        setUser(null);
      } finally {
        setAuthChecking(false);
      }
    }
    checkAuth();
  }, []);

  const selectedRoute =
    routeData?.routes.find(
      (route) => route.route_index === selectedRouteIndex
    ) ?? null;

  const handleRoutesFound = (data: RouteSearchResponse) => {
    setRouteData(data);
    if (data.routes.length > 0) {
      setSelectedRouteIndex(data.routes[0].route_index);
    } else {
      setSelectedRouteIndex(null);
    }
    setShowResults(true);
  };

  const handleNewSearch = () => {
    setShowResults(false);
    setRouteData(null);
    setSelectedRouteIndex(null);
    setIsNavigating(false);
    setActiveTripId(null);
    setUserLiveCoords(null);
    setSearchResetKey((val) => val + 1);
  };

  // Launch Live GPS Navigation
  const handleStartNavigation = async (route: RouteResult) => {
    if (!routeData) return;

    try {
      const today = new Date().toISOString().split("T")[0];
      const timeStr = `${String(new Date().getHours()).padStart(2, "0")}:${String(new Date().getMinutes()).padStart(2, "0")}`;

      const tripPayload = {
        travel_date: today,
        travel_time: timeStr,
        source_zone: routeData.source.name.split(",")[0] || "Chennai Origin",
        destination_zone: routeData.destination.name.split(",")[0] || "Chennai Destination",
        source_lat: routeData.source.latitude,
        source_lon: routeData.source.longitude,
        dest_lat: routeData.destination.latitude,
        dest_lon: routeData.destination.longitude,
        selected_route_id: route.route_index,
        selected_distance_km: route.distance_km,
        selected_safety_score: route.personalized_safety_score ?? route.safety_score,
        interactions: routeData.routes.map((r) => ({
          route_id: r.route_index,
          route_rank: r.rank,
          route_distance_km: r.distance_km,
          route_risk: r.personalized_risk ?? r.final_risk,
          route_safety_score: r.personalized_safety_score ?? r.safety_score,
          selected: r.route_index === route.route_index,
          rejected: r.route_index !== route.route_index,
        })),
      };

      const created = await createTrip(tripPayload);
      const tripId = created.id;

      await startNavigation({
        trip_id: tripId,
        selected_route_index: route.route_index,
        geometry: route.geometry,
        instructions: route.instructions,
        destination_lat: routeData.destination.latitude,
        dest_lon: routeData.destination.longitude,
      });

      setActiveTripId(tripId);
      setIsNavigating(true);
    } catch (err) {
      console.error("Failed to start navigation:", err);
    }
  };

  const handleRouteRecalculated = (newRoute: RouteResult) => {
    if (!routeData) return;
    setRouteData({
      ...routeData,
      routes: [newRoute, ...routeData.routes.filter((r) => r.route_index !== newRoute.route_index)],
    });
    setSelectedRouteIndex(newRoute.route_index);
  };

  const handleEndTrip = () => {
    const finishedId = activeTripId;
    setIsNavigating(false);
    setActiveTripId(null);
    setUserLiveCoords(null);
    if (finishedId) {
      setCompletedTripId(finishedId);
    }
  };

  // Sign out handler
  const handleLogout = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("saferoute_token");
    }
    setUser(null);
    setShowResults(false);
    setRouteData(null);
    setIsNavigating(false);
    setActiveTripId(null);
  };

  // 1. Initial Authentication Check Loader
  if (authChecking) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-900 text-slate-100">
        <div className="flex flex-col items-center gap-4">
          <SafeRouteLogo className="w-16 h-16 animate-pulse" />
          <h2 className="text-2xl font-bold tracking-tight text-white">SafeRoute</h2>
          <p className="text-xs font-medium text-emerald-400">
            Initializing Chennai Safety Engine...
          </p>
        </div>
      </div>
    );
  }

  // 2. Unauthenticated: Display Login/Registration Page with logo & 1-line text
  if (!user) {
    return (
      <LoginPage
        onLoginSuccess={(loggedInUser) => {
          setUser(loggedInUser);
        }}
      />
    );
  }

  // 3. Authenticated: Display Map, Search Bar, and Navigation HUD
  return (
    <main className="relative h-screen w-screen overflow-hidden">
      {/* Top Header / Account Controls with Sign Out Logo Button */}
      <div className="absolute right-6 top-6 z-[1000] flex items-center gap-2.5">
        <div className="flex items-center gap-2 rounded-2xl bg-white/95 px-3 py-1.5 shadow-2xl backdrop-blur-xl text-xs border border-gray-100">
          {/* User profile avatar badge */}
          <div className="flex items-center gap-2 border-r border-gray-200/80 pr-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white font-bold text-xs shadow-sm shadow-emerald-500/30">
              {user.name ? user.name.charAt(0).toUpperCase() : "U"}
            </div>
            <div className="flex flex-col text-left">
              <span className="font-bold text-gray-900 leading-tight">{user.name}</span>
              <span className="text-[10px] text-emerald-600 font-semibold leading-tight flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 inline-block animate-pulse"></span>
                Chennai
              </span>
            </div>
          </div>

          {/* Dashboard Button */}
          <button
            onClick={() => setShowDashboardModal(true)}
            className="rounded-xl bg-emerald-50 px-2.5 py-1.5 font-semibold text-emerald-700 hover:bg-emerald-100 transition flex items-center gap-1.5 border border-emerald-100"
            title="Dashboard & Past Trips"
          >
            <span>📊</span> Dashboard
          </button>

          {/* Digital Twin Button */}
          <button
            onClick={() => setShowPreferencesModal(true)}
            className="rounded-xl bg-purple-50 px-2.5 py-1.5 font-semibold text-purple-700 hover:bg-purple-100 transition flex items-center gap-1.5 border border-purple-100"
            title="Personal Preferences & Digital Twin"
          >
            <span>🧬</span> Twin
          </button>

          {/* Profile & Trusted Contacts Button */}
          <button
            onClick={() => setShowEmergencyModal(true)}
            className="rounded-xl bg-red-50 px-2.5 py-1.5 font-bold text-red-700 hover:bg-red-100 transition flex items-center gap-1.5 border border-red-200"
            title="Profile, Trusted Contacts & Emergency SOS Logs"
          >
            <span>🛡️</span> Profile & Contacts
          </button>

          {/* Sign Out Logo Button */}
          <button
            onClick={handleLogout}
            className="group flex h-8 w-8 items-center justify-center rounded-xl bg-gray-100 text-gray-600 hover:bg-red-50 hover:text-red-600 hover:border-red-200 border border-transparent transition"
            title="Sign Out"
            aria-label="Sign Out"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-4 h-4 transition group-hover:scale-110"
            >
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Map with custom Source, Destination & Live GPS Markers */}
      <SafeRouteMap
        routes={routeData?.routes ?? []}
        selectedRouteIndex={selectedRouteIndex}
        source={routeData?.source ?? null}
        destination={routeData?.destination ?? null}
        userLocation={userLiveCoords}
      />

      {/* Search Panel (displayed after login, hidden during active navigation) */}
      {!showResults && !isNavigating && (
        <SearchPanel
          onRoutesFound={handleRoutesFound}
          resetKey={searchResetKey}
        />
      )}

      {/* Route Results & Details Panel */}
      {showResults && !isNavigating && routeData && routeData.routes.length > 0 && (
        <aside className="absolute bottom-5 left-5 top-5 z-[1000] w-[380px] overflow-y-auto rounded-3xl bg-white/95 p-4 shadow-2xl backdrop-blur-xl border border-gray-100">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">SafeRoute</h1>
              <p className="text-xs text-emerald-700 font-medium">
                Personalized Chennai Safety Alternatives
              </p>
            </div>
            <button
              onClick={handleNewSearch}
              className="flex h-8 w-8 items-center justify-center rounded-full text-xl text-gray-500 hover:bg-gray-100 hover:text-gray-900 transition"
              title="New search"
            >
              ×
            </button>
          </div>

          <RouteDetails
            route={selectedRoute}
            onStartNavigation={handleStartNavigation}
          />

          <div className="my-5 border-t border-gray-200" />

          <RouteList
            routes={routeData.routes}
            selectedRouteIndex={selectedRouteIndex}
            onSelectRoute={setSelectedRouteIndex}
          />
        </aside>
      )}

      {/* Live GPS Navigation HUD */}
      {isNavigating && activeTripId && selectedRoute && (
        <NavigationHUD
          tripId={activeTripId}
          route={selectedRoute}
          onEndTrip={handleEndTrip}
          onRouteUpdated={handleRouteRecalculated}
          onUserLocationUpdate={setUserLiveCoords}
        />
      )}

      {/* Modals */}
      {showPreferencesModal && (
        <PreferencesModal
          onClose={() => setShowPreferencesModal(false)}
        />
      )}

      {showDashboardModal && (
        <DashboardModal
          onClose={() => setShowDashboardModal(false)}
        />
      )}

      <EmergencyModal
        isOpen={showEmergencyModal}
        onClose={() => setShowEmergencyModal(false)}
        user={user}
      />

      {completedTripId && (
        <TripFeedbackModal
          tripId={completedTripId}
          onClose={() => setCompletedTripId(null)}
          onFeedbackSubmitted={() => {
            setShowDashboardModal(true);
          }}
        />
      )}
    </main>
  );
}