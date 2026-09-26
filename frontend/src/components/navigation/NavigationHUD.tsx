"use client";

import { useEffect, useState, useRef } from "react";
import type { RouteResult, NavigationStatus } from "../../types/route";
import { updateGPSLocation, startNavigation, endNavigation } from "../../services/routeApi";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getSOSHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("saferoute_token") || localStorage.getItem("token")
      : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = "Bearer " + token;
  return headers;
}

function copyTextSafe(text: string): boolean {
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text);
      return true;
    }
  } catch {}
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    return true;
  } catch {
    return false;
  }
}

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
  const [isReroutingAlert, setIsReroutingAlert] = useState(false);

  // SOS Emergency Subsystem State
  const [showSOSConfirm, setShowSOSConfirm] = useState(false);
  const [sosNotes, setSosNotes] = useState("");
  const [sosTriggering, setSosTriggering] = useState(false);
  const [activeSOS, setActiveSOS] = useState<any | null>(null);
  const [sosBannerMessage, setSosBannerMessage] = useState<string | null>(null);

  const routeGeometry = route.geometry;
  const simIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const activeSOSRef = useRef<any | null>(null);
  const wasSimulatingBeforeSOSRef = useRef<boolean>(false);
  const simStepIndexRef = useRef<number>(0);

  activeSOSRef.current = activeSOS;
  simStepIndexRef.current = simStepIndex;

  const stopMovementInterval = () => {
    if (simIntervalRef.current) {
      clearInterval(simIntervalRef.current);
      simIntervalRef.current = null;
    }
    setSimulating(false);
  };

  const startMovementInterval = () => {
    if (simIntervalRef.current) clearInterval(simIntervalRef.current);
    setSimulating(true);
    let idx = simStepIndexRef.current;

    simIntervalRef.current = setInterval(() => {
      // Do NOT move if SOS confirmation or Active SOS is open!
      if (activeSOSRef.current) {
        return;
      }

      idx += 1;
      if (idx >= routeGeometry.length - 1) {
        stopMovementInterval();
        const [destLon, destLat] = routeGeometry[routeGeometry.length - 1];
        onUserLocationUpdate([destLat, destLon]);
        sendGPS(destLat, destLon, 0.0);
        setTimeout(() => {
          handleEndTrip();
        }, 1200);
        return;
      }

      setSimStepIndex(idx);
      simStepIndexRef.current = idx;
      const [lon, lat] = routeGeometry[idx];
      onUserLocationUpdate([lat, lon]);
      sendGPS(lat, lon, 30.0);
    }, 2500);
  };

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
      setIsReroutingAlert(status.rerouting);

      if (status.new_route) {
        onRouteUpdated(status.new_route);
      }

      if (status.is_at_destination) {
        stopMovementInterval();
        setTimeout(() => {
          handleEndTrip();
        }, 1200);
      }
    } catch (err) {
      if (routeGeometry.length > 0) {
        const [destLon, destLat] = routeGeometry[routeGeometry.length - 1];
        startNavigation({
          trip_id: tripId,
          selected_route_index: route.route_index ?? 0,
          geometry: routeGeometry,
          instructions: route.instructions || [],
          destination_lat: destLat,
          dest_lon: destLon,
        }).catch(() => {});
      }
    }
  };

  // Start / stop simulation along the route
  const toggleSimulation = () => {
    if (activeSOS) {
      alert("Movement is paused while SOS is active. Click 'Cancel SOS' or 'Mark Safe' to resume movement.");
      return;
    }
    if (simulating) {
      stopMovementInterval();
    } else {
      startMovementInterval();
    }
  };

  // Simulate deliberate off-route deviation to trigger automatic re-routing
  const triggerOffRouteDeviation = () => {
    if (activeSOS) return;
    if (routeGeometry.length > 0) {
      const [lon, lat] = routeGeometry[Math.min(simStepIndex + 2, routeGeometry.length - 1)];
      const offLat = lat + 0.003;
      const offLon = lon - 0.003;
      onUserLocationUpdate([offLat, offLon]);
      sendGPS(offLat, offLon, 20.0);
    }
  };

  const handleEndTrip = async () => {
    stopMovementInterval();
    try {
      await endNavigation(tripId);
    } catch {
      // ignore
    }
    onEndTrip();
  };

  const getCurrentLatLon = (): [number, number] => {
    if (routeGeometry.length > 0) {
      const idx = Math.min(simStepIndex, routeGeometry.length - 1);
      const [lon, lat] = routeGeometry[idx];
      return [lat, lon];
    }
    return [13.0827, 80.2707];
  };

  // When user clicks SOS button, immediately pause movement
  const handleOpenSOSConfirm = () => {
    wasSimulatingBeforeSOSRef.current = simulating;
    stopMovementInterval();
    setShowSOSConfirm(true);
  };

  const handleCancelSOSModal = () => {
    setShowSOSConfirm(false);
    if (wasSimulatingBeforeSOSRef.current && !activeSOS) {
      startMovementInterval();
    }
  };

  const handleConfirmTriggerSOS = async () => {
    setSosTriggering(true);
    stopMovementInterval(); // Keep user halted at emergency coordinates
    try {
      const [lat, lon] = getCurrentLatLon();
      const res = await fetch(`${API_BASE}/api/sos/activate`, {
        method: "POST",
        headers: getSOSHeaders(),
        body: JSON.stringify({
          trip_id: String(tripId),
          route_id: String(route.route_index ?? "0"),
          latitude: lat,
          longitude: lon,
          speed: 0.0,
          trigger_type: "manual",
          user_notes: sosNotes || "Triggered emergency SOS during active trip",
        }),
      });
      const data = await res.json();
      setActiveSOS(data);
      activeSOSRef.current = data;
      setShowSOSConfirm(false);
      setSosBannerMessage("🚨 SOS ACTIVE - Movement paused at emergency spot & trusted contacts alerted");
    } catch (e: any) {
      alert(e.message || "Failed to trigger SOS");
    } finally {
      setSosTriggering(false);
    }
  };

  const handleResolveSOS = async (status: "resolved" | "cancelled") => {
    if (!activeSOS?.sos_id) return;
    try {
      await fetch(`${API_BASE}/api/sos/${activeSOS.sos_id}/${status === "resolved" ? "resolve" : "cancel"}`, {
        method: "POST",
        headers: getSOSHeaders(),
        body: JSON.stringify({ resolution_notes: status }),
      });
      setActiveSOS(null);
      activeSOSRef.current = null;
      setSosBannerMessage(
        status === "resolved"
          ? "✅ Marked Safe - SOS Resolved & Navigation Resumed"
          : "SOS Cancelled - Navigation Movement Resumed"
      );
      setTimeout(() => setSosBannerMessage(null), 4000);

      // Resume location movement after Cancel SOS / Mark Safe!
      if (wasSimulatingBeforeSOSRef.current) {
        startMovementInterval();
      }
    } catch (e: any) {
      alert(e.message || "Failed to update SOS status");
    }
  };

  const handleShareLiveLink = () => {
    if (!activeSOS) return;
    const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
    const token = activeSOS.share_token || String(activeSOS.tracking_url || "").split("/").pop();
    const liveUrl = token ? `${origin}/sos/track/${token}` : (activeSOS.tracking_url || origin);

    copyTextSafe(liveUrl);
    // Open the Live SOS Tracking Page in a new tab so the user/contact sees the live emergency dashboard immediately
    window.open(liveUrl, "_blank");
  };

  const handleSendDirectSMSOrWhatsApp = () => {
    if (!activeSOS) return;
    const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
    const token = activeSOS.share_token || String(activeSOS.tracking_url || "").split("/").pop();
    const liveUrl = token ? `${origin}/sos/track/${token}` : (activeSOS.tracking_url || origin);
    const contactPhone =
      activeSOS.notified_contacts?.[0]?.phone_number?.replace(/[^0-9+]/g, "") || "";
    const textMsg = encodeURIComponent(
      `?? EMERGENCY SOS! I need help near ${activeSOS.road_name || "Chennai Road"} (${Number(activeSOS.latitude).toFixed(5)}, ${Number(activeSOS.longitude).toFixed(5)}). Nearest Police: ${activeSOS.nearest_police_station?.name || "Police Station"}. Track my live location here: ${liveUrl}`
    );
    if (contactPhone) {
      window.open(`https://wa.me/${contactPhone.replace("+", "")}?text=${textMsg}`, "_blank");
    } else {
      window.open(`sms:?body=${textMsg}`, "_self");
    }
  };

  return (
    <div className="absolute left-5 right-5 top-5 z-[1000] mx-auto max-w-lg space-y-3">
      {/* Destination Reached Alert */}
      {navStatus?.is_at_destination && (
        <div className="flex items-center gap-2 rounded-xl bg-emerald-600 p-3 text-xs font-semibold text-white shadow-lg animate-pulse">
          <span>🏁</span>
          <span>You have reached your destination! Completing trip & opening feedback...</span>
        </div>
      )}

      {/* Off-Route / Re-routing Warning Alert */}
      {isReroutingAlert && !navStatus?.is_at_destination && (
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
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide">
                {activeSOS
                  ? "🚨 MOVEMENT HALTED ? SOS ACTIVE"
                  : navStatus?.distance_to_turn_formatted
                  ? `In ${navStatus.distance_to_turn_formatted}`
                  : "Next Direction"}
              </p>
              <button
                onClick={handleOpenSOSConfirm}
                className="rounded-xl bg-red-600 hover:bg-red-500 px-3 py-1 text-xs font-extrabold text-white shadow-lg shadow-red-500/40 animate-pulse flex items-center gap-1 border border-red-400"
              >
                <span>🚨</span>
                <span>EMERGENCY SOS</span>
              </button>
            </div>
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
              {activeSOS ? "0 km/h (SOS Paused)" : simulating ? "30 km/h" : "Live GPS"}
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="mt-4 flex gap-2">
          <button
            onClick={toggleSimulation}
            disabled={!!activeSOS}
            className={`flex-1 rounded-xl py-2.5 text-xs font-semibold transition ${
              activeSOS
                ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                : simulating
                ? "bg-amber-100 text-amber-800 hover:bg-amber-200"
                : "bg-gray-100 text-gray-800 hover:bg-gray-200"
            }`}
          >
            {activeSOS ? "⏸ Paused for SOS" : simulating ? "⏸ Pause Movement" : "▶ Simulate GPS Drive"}
          </button>

          <button
            onClick={triggerOffRouteDeviation}
            disabled={!!activeSOS}
            title="Simulates vehicle driving off-course to verify dynamic re-routing"
            className="rounded-xl border border-gray-200 px-3 py-2.5 text-xs font-semibold text-gray-600 hover:bg-gray-50 disabled:opacity-40"
          >
            Simulate Deviation
          </button>

          <button
            onClick={handleOpenSOSConfirm}
            className="rounded-xl bg-red-600 px-3.5 py-2.5 text-xs font-extrabold text-white shadow-md shadow-red-500/30 transition hover:bg-red-700"
          >
            🚨 SOS
          </button>

          <button
            onClick={handleEndTrip}
            className="rounded-xl bg-gray-800 px-4 py-2.5 text-xs font-semibold text-white shadow transition hover:bg-gray-900"
          >
            End Trip
          </button>
        </div>
      </div>

      {/* SOS Confirmation Modal */}
      {showSOSConfirm && (
        <div className="rounded-2xl bg-red-950 text-white p-4 shadow-2xl border-2 border-red-500">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-extrabold text-sm uppercase tracking-wider text-red-200">
              🚨 Trigger Emergency SOS? (Movement Paused)
            </h4>
            <button
              onClick={handleCancelSOSModal}
              className="text-xs text-red-300 hover:text-white"
            >
              ✕ Close
            </button>
          </div>
          <p className="text-xs text-red-100 mb-3">
            Your movement simulation is now paused. Confirming SOS will log an emergency event, notify your trusted contacts with a live tracking link, and locate the nearest Chennai police station.
          </p>
          <input
            type="text"
            value={sosNotes}
            onChange={(e) => setSosNotes(e.target.value)}
            placeholder="Optional note (e.g., Broken street light, being followed)..."
            className="w-full text-xs bg-red-900/60 border border-red-700 rounded-lg p-2 text-white placeholder-red-300 mb-3 focus:outline-none"
          />
          <div className="flex space-x-2">
            <button
              onClick={handleConfirmTriggerSOS}
              disabled={sosTriggering}
              className="flex-1 bg-red-600 hover:bg-red-500 text-white font-bold py-2 px-3 rounded-lg text-xs shadow transition disabled:opacity-50"
            >
              {sosTriggering ? "Triggering SOS..." : "🚨 CONFIRM SOS NOW"}
            </button>
            <button
              onClick={handleCancelSOSModal}
              className="bg-gray-800 hover:bg-gray-700 text-gray-200 font-semibold py-2 px-3 rounded-lg text-xs transition"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Active SOS Emergency Card */}
      {activeSOS && (
        <div className="rounded-2xl bg-red-900 text-white p-4 shadow-2xl border-2 border-red-400">
          <div className="flex items-center justify-between">
            <span className="font-extrabold text-xs uppercase tracking-wider bg-red-600 px-2.5 py-1 rounded-full animate-pulse">
              🚨 SOS ACTIVE (#{String(activeSOS.sos_id).slice(0, 8)})
            </span>
            <span className="text-xs text-red-200 font-medium">
              Road: {activeSOS.road_name || "Snapped to Route"}
            </span>
          </div>

          {activeSOS.nearest_police_station && (
            <div className="mt-3 bg-red-950/80 p-3 rounded-lg border border-red-700 text-xs">
              <div className="text-red-300 font-semibold uppercase">Nearest Police Help</div>
              <div className="font-bold text-white text-sm mt-0.5">
                🚓 {activeSOS.nearest_police_station.name} ({activeSOS.nearest_police_station.distance_km} km)
              </div>
              <div className="text-red-200 mt-1">
                Emergency Line: <strong>{activeSOS.nearest_police_station.phone}</strong>
              </div>
            </div>
          )}

          {activeSOS.notified_contacts && activeSOS.notified_contacts.length > 0 ? (
            <div className="mt-2 text-xs text-red-100 flex items-center justify-between">
              <span>
                Notified Contacts:{" "}
                <strong>
                  {activeSOS.notified_contacts
                    .map((c: any) => `${c.contact_name} (${c.phone_number})`)
                    .join(", ")}
                </strong>
              </span>
              <button
                onClick={handleSendDirectSMSOrWhatsApp}
                className="ml-2 bg-emerald-600 hover:bg-emerald-500 text-white px-2.5 py-1 rounded-lg text-[11px] font-bold shrink-0 shadow"
              >
                💬 Send WhatsApp/SMS
              </button>
            </div>
          ) : (
            <div className="mt-2 text-xs text-amber-200">
              No trusted contacts configured yet (Add in 🛡️ Profile & Contacts). Emergency logged on server.
            </div>
          )}

          <div className="mt-3 grid grid-cols-2 gap-2">
            <a
              href="tel:112"
              className="bg-white text-red-900 font-extrabold py-2 px-3 rounded-lg text-xs text-center shadow hover:bg-red-50 transition"
            >
              📞 Call 112 Police
            </a>
            <button
              onClick={handleShareLiveLink}
              className="bg-red-700 hover:bg-red-600 text-white font-bold py-2 px-3 rounded-lg text-xs transition"
            >
              🔗 Open & Copy Live Link
            </button>
            <button
              onClick={() => handleResolveSOS("resolved")}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-3 rounded-lg text-xs transition"
            >
              ✅ Mark Safe (Resume)
            </button>
            <button
              onClick={() => handleResolveSOS("cancelled")}
              className="bg-gray-800 hover:bg-gray-700 text-gray-200 font-semibold py-2 px-3 rounded-lg text-xs transition"
            >
              ✕ Cancel SOS (Resume)
            </button>
          </div>
        </div>
      )}

      {sosBannerMessage && !activeSOS && (
        <div className="bg-emerald-800 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow border border-emerald-500">
          {sosBannerMessage}
        </div>
      )}
    </div>
  );
}
