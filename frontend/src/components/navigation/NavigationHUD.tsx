"use client";

import { useEffect, useState, useRef } from "react";
import type { RouteResult, NavigationStatus } from "../../types/route";
import { updateGPSLocation, startNavigation, endNavigation, manualReroute } from "../../services/routeApi";

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
  const [isSirenActive, setIsSirenActive] = useState(false);

  // Audio Context Ref for Siren
  const audioCtxRef = useRef<AudioContext | null>(null);
  const oscRef = useRef<OscillatorNode | null>(null);
  const sirenIntervalRef = useRef<any>(null);

  const activeSOSRef = useRef<any | null>(null);
  activeSOSRef.current = activeSOS;

  const simIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const simStepIndexRef = useRef<number>(0);
  simStepIndexRef.current = simStepIndex;
  const wasSimulatingBeforeSOSRef = useRef<boolean>(false);

  // Convert geometry coords for simulation traversal
  const routeGeometry = (route.geometry || []).map((pt: any) =>
    Array.isArray(pt) ? [pt[0], pt[1]] : [pt.lon, pt.lat]
  ) as [number, number][];

  const stopSiren = () => {
    try {
      if (sirenIntervalRef.current) {
        clearInterval(sirenIntervalRef.current);
        sirenIntervalRef.current = null;
      }
      oscRef.current?.stop();
      audioCtxRef.current?.close();
    } catch {}
    oscRef.current = null;
    audioCtxRef.current = null;
    setIsSirenActive(false);
  };

  const toggleSiren = () => {
    if (isSirenActive) {
      stopSiren();
    } else {
      try {
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        if (!AudioContextClass) {
          alert("Audio API not supported on this browser.");
          return;
        }
        const ctx = new AudioContextClass();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sawtooth";
        gain.gain.setValueAtTime(0.8, ctx.currentTime);

        let high = false;
        osc.frequency.setValueAtTime(750, ctx.currentTime);
        sirenIntervalRef.current = setInterval(() => {
          if (ctx.state === "closed") return;
          const t = ctx.currentTime;
          osc.frequency.linearRampToValueAtTime(high ? 750 : 1250, t + 0.35);
          high = !high;
        }, 350);

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();

        audioCtxRef.current = ctx;
        oscRef.current = osc;
        setIsSirenActive(true);
      } catch (e: any) {
        alert("Could not start siren: " + e.message);
      }
    }
  };

  // Start navigation session on mount
  useEffect(() => {
    if (routeGeometry.length > 0) {
      const [destLon, destLat] = routeGeometry[routeGeometry.length - 1];
      startNavigation({
        trip_id: tripId,
        selected_route_index: route.route_index ?? 0,
        geometry: routeGeometry,
        instructions: route.instructions || [],
        destination_lat: destLat,
        dest_lon: destLon,
      }).catch((err) => {
        console.error("Failed to initialize navigation session:", err);
      });
    }

    return () => {
      stopMovementInterval();
      stopSiren();
      endNavigation(tripId).catch(() => {});
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

  const startMovementInterval = () => {
    if (simIntervalRef.current) clearInterval(simIntervalRef.current);
    setSimulating(true);

    simIntervalRef.current = setInterval(() => {
      if (activeSOSRef.current) {
        return;
      }

      const next = simStepIndexRef.current + 1;
      if (next >= routeGeometry.length) {
        stopMovementInterval();
        const lastPoint = routeGeometry[routeGeometry.length - 1];
        if (lastPoint) {
          onUserLocationUpdate([lastPoint[1], lastPoint[0]]);
          sendGPS(lastPoint[1], lastPoint[0], 0.0);
        }
        return;
      }

      simStepIndexRef.current = next;
      setSimStepIndex(next);

      const point = routeGeometry[next];
      if (point) {
        const [lon, lat] = point;
        onUserLocationUpdate([lat, lon]);
        sendGPS(lat, lon, 28.0);
      }
    }, 2000);
  };

  const stopMovementInterval = () => {
    if (simIntervalRef.current) {
      clearInterval(simIntervalRef.current);
      simIntervalRef.current = null;
    }
    setSimulating(false);
  };

  const toggleSimulation = () => {
    if (activeSOS) return;
    if (simulating) {
      stopMovementInterval();
    } else {
      startMovementInterval();
    }
  };

  const handleSimulateOffRoute = () => {
    if (activeSOS) return;
    const currentPoint = routeGeometry[simStepIndex] || routeGeometry[0];
    const offLat = currentPoint[1] + 0.0035;
    const offLon = currentPoint[0] + 0.0035;

    onUserLocationUpdate([offLat, offLon]);
    sendGPS(offLat, offLon, 15.0);
  };

  const handleEndTrip = () => {
    stopMovementInterval();
    stopSiren();
    endNavigation(tripId).catch(() => {});
    onEndTrip();
  };

  const handleTriggerSOSClick = () => {
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
    try {
      const currentPoint = routeGeometry[simStepIndex] || routeGeometry[0];
      const lat = currentPoint ? currentPoint[1] : 13.0827;
      const lon = currentPoint ? currentPoint[0] : 80.2707;

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
      setSosBannerMessage("\u{1F6A8} SOS ACTIVE - Location locked at emergency spot & trusted contacts alerted");
    } catch (e: any) {
      alert(e.message || "Failed to trigger SOS");
    } finally {
      setSosTriggering(false);
    }
  };

  const handleResolveSOS = async (status: "resolved" | "cancelled") => {
    if (!activeSOS?.sos_id) return;
    try {
      stopSiren();
      await fetch(`${API_BASE}/api/sos/${activeSOS.sos_id}/${status === "resolved" ? "resolve" : "cancel"}`, {
        method: "POST",
        headers: getSOSHeaders(),
        body: JSON.stringify({ resolution_notes: status }),
      });
      setActiveSOS(null);
      activeSOSRef.current = null;
      setSosBannerMessage(
        status === "resolved"
          ? "\u{2705} Marked Safe - SOS Resolved & Navigation Resumed"
          : "SOS Cancelled - Navigation Movement Resumed"
      );
      setTimeout(() => setSosBannerMessage(null), 4000);

      if (wasSimulatingBeforeSOSRef.current) {
        startMovementInterval();
      }
    } catch (e: any) {
      alert(e.message || "Failed to update SOS status");
    }
  };

  const handleMarkRouteUnsafe = async () => {
    if (!activeSOS?.sos_id) return;
    try {
      stopSiren();
      await fetch(`${API_BASE}/api/sos/${activeSOS.sos_id}/mark-unsafe`, {
        method: "POST",
        headers: getSOSHeaders(),
        body: JSON.stringify({ resolution_notes: "Reported route/corridor as unsafe" }),
      });

      setSosBannerMessage("\u{26A0}\u{FE0F} Route Marked Unsafe \u{2014} Recalculating Safe Route & Diverting...");

      // Recalculate route avoiding this stretch
      const currentPoint = routeGeometry[simStepIndex] || routeGeometry[0];
      const [destLon, destLat] = routeGeometry[routeGeometry.length - 1];
      try {
        const rerouteRes = await manualReroute({
          trip_id: tripId,
          current_lat: currentPoint[1],
          current_lon: currentPoint[0],
          destination_lat: destLat,
          dest_lon: destLon,
        });
        if (rerouteRes?.new_route) {
          onRouteUpdated(rerouteRes.new_route);
        }
      } catch (err) {
        console.warn("Auto-reroute attempt failed, resuming standard guidance:", err);
      }

      setActiveSOS(null);
      activeSOSRef.current = null;
      setTimeout(() => setSosBannerMessage(null), 5000);

      if (wasSimulatingBeforeSOSRef.current) {
        startMovementInterval();
      }
    } catch (e: any) {
      alert(e.message || "Failed to mark route as unsafe");
    }
  };

  const getEmergencyMessage = (liveUrl: string) => {
    return (
      `\u{1F6A8} EMERGENCY SOS! I need help near ${activeSOS?.road_name || "Chennai Monitored Corridor"} ` +
      `(${Number(activeSOS?.latitude).toFixed(5)}, ${Number(activeSOS?.longitude).toFixed(5)}). ` +
      `Nearest Police: ${activeSOS?.nearest_police_station?.name || "Police Station"}. ` +
      `Track my live location here: ${liveUrl}`
    );
  };

  const handleShareLiveLink = () => {
    if (!activeSOS) return;
    const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
    const token = activeSOS.share_token || String(activeSOS.tracking_url || "").split("/").pop();
    const liveUrl = token ? `${origin}/sos/track/${token}` : (activeSOS.tracking_url || origin);

    copyTextSafe(liveUrl);
    window.open(liveUrl, "_blank");
  };

  const handleSendWhatsApp = (phone: string) => {
    if (!activeSOS) return;
    const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
    const token = activeSOS.share_token || String(activeSOS.tracking_url || "").split("/").pop();
    const liveUrl = token ? `${origin}/sos/track/${token}` : (activeSOS.tracking_url || origin);
    const cleanPhone = phone.replace(/[^0-9]/g, "");
    const formattedPhone = cleanPhone.startsWith("91") ? cleanPhone : `91${cleanPhone.slice(-10)}`;
    const textMsg = encodeURIComponent(getEmergencyMessage(liveUrl));
    window.open(`https://wa.me/${formattedPhone}?text=${textMsg}`, "_blank");
  };

  const handleSendSMS = (phone: string) => {
    if (!activeSOS) return;
    const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
    const token = activeSOS.share_token || String(activeSOS.tracking_url || "").split("/").pop();
    const liveUrl = token ? `${origin}/sos/track/${token}` : (activeSOS.tracking_url || origin);
    const cleanPhone = phone.replace(/[^0-9]/g, "").slice(-10);
    const textMsg = encodeURIComponent(getEmergencyMessage(liveUrl));
    window.open(`sms:${cleanPhone}?body=${textMsg}`, "_self");
  };

  const handleBroadcastAllSMS = () => {
    if (!activeSOS || !activeSOS.notified_contacts?.length) return;
    const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
    const token = activeSOS.share_token || String(activeSOS.tracking_url || "").split("/").pop();
    const liveUrl = token ? `${origin}/sos/track/${token}` : (activeSOS.tracking_url || origin);
    const phones = activeSOS.notified_contacts
      .map((c: any) => c.phone_number?.replace(/[^0-9]/g, "").slice(-10))
      .filter(Boolean);
    const textMsg = encodeURIComponent(getEmergencyMessage(liveUrl));
    window.open(`sms:${phones.join(",")}?body=${textMsg}`, "_self");
  };

  const handleEscapeToPoliceStation = () => {
    if (!activeSOS?.nearest_police_station?.lat || !activeSOS?.nearest_police_station?.lon) return;
    const pLat = activeSOS.nearest_police_station.lat;
    const pLon = activeSOS.nearest_police_station.lon;
    const gmapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${pLat},${pLon}&travelmode=walking`;
    window.open(gmapsUrl, "_blank");
  };

  return (
    <div className="absolute left-5 right-5 top-5 z-[1000] mx-auto max-w-lg space-y-3">
      {/* Destination Reached Alert */}
      {navStatus?.is_at_destination && (
        <div className="flex items-center gap-2 rounded-xl bg-emerald-600 p-3 text-xs font-semibold text-white shadow-lg animate-pulse">
          <span>{"\u{1F3C1}"}</span>
          <span>You have reached your destination! Completing trip & opening feedback...</span>
        </div>
      )}

      {/* Off-Route / Re-routing Warning Alert */}
      {isReroutingAlert && !navStatus?.is_at_destination && (
        <div className="flex items-center gap-2 rounded-xl bg-amber-500 p-3 text-xs font-semibold text-white shadow-lg animate-pulse">
          <span>{"\u{1F504}"}</span>
          <span>Off-route detected. Automatically calculating new safe route from current position...</span>
        </div>
      )}

      {/* Main Navigation Heads-Up Display */}
      <div className="rounded-2xl bg-white/95 p-4 shadow-2xl backdrop-blur border border-gray-100">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-xl font-bold text-white shadow-md">
            {"\u{1F9ED}"}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                {activeSOS
                  ? "\u{1F6A8} MOVEMENT HALTED \u{2022} SOS ACTIVE"
                  : isReroutingAlert
                  ? "Recalculating..."
                  : "Turn Guidance"}
              </span>
              <button
                onClick={handleTriggerSOSClick}
                className="bg-red-600 hover:bg-red-700 text-white font-extrabold text-[11px] px-2.5 py-1 rounded-full shadow animate-pulse flex items-center gap-1"
                title="Immediate Emergency SOS"
              >
                <span>{"\u{1F6A8}"}</span> EMERGENCY SOS
              </button>
            </div>
            <h2 className="text-base font-extrabold text-gray-900 truncate mt-0.5">
              {navStatus?.current_instruction || (typeof route.instructions?.[0] === "string" ? route.instructions[0] : (route.instructions?.[0] as any)?.instruction) || "Follow highlighted safe route"}
            </h2>
            {navStatus?.next_instruction && (
              <p className="text-xs font-medium text-gray-500 truncate mt-0.5">
                Then: {navStatus.next_instruction}
              </p>
            )}
          </div>
        </div>

        {/* Live Trip Telemetry */}
        <div className="mt-3.5 grid grid-cols-3 gap-2 border-t border-gray-100 pt-3 text-center">
          <div>
            <span className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider">
              Remaining
            </span>
            <span className="text-sm font-extrabold text-gray-800">
              {navStatus ? `${navStatus.remaining_distance_km.toFixed(2)} km` : `${route.distance_km} km`}
            </span>
          </div>
          <div>
            <span className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider">
              Est. Time
            </span>
            <span className="text-sm font-extrabold text-gray-800">
              {navStatus ? `${navStatus.eta_minutes.toFixed(1)} min` : `${(route.distance_km * 2.5).toFixed(1)} min`}
            </span>
          </div>
          <div>
            <span className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider">
              Speed
            </span>
            <span className="text-sm font-extrabold text-gray-800">
              {activeSOS ? "0 km/h (SOS Paused)" : simulating ? "28 km/h" : "Live GPS"}
            </span>
          </div>
        </div>

        {/* Navigation Action Buttons */}
        <div className="mt-4 flex gap-2">
          <button
            onClick={toggleSimulation}
            disabled={!!activeSOS}
            className={`flex-1 rounded-xl py-2 px-3 text-xs font-bold transition shadow-sm ${
              activeSOS
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : simulating
                ? "bg-amber-100 text-amber-800 hover:bg-amber-200"
                : "bg-blue-600 text-white hover:bg-blue-700"
            }`}
          >
            {activeSOS ? "\u{23F8}\u{FE0F} Paused for SOS" : simulating ? "\u{23F8}\u{FE0F} Pause Movement" : "\u{25B6}\u{FE0F} Simulate GPS Drive"}
          </button>

          <button
            onClick={handleSimulateOffRoute}
            disabled={!!activeSOS}
            className={`rounded-xl py-2 px-3 text-xs font-bold border transition ${
              activeSOS
                ? "border-gray-200 text-gray-300 cursor-not-allowed"
                : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
            }`}
            title="Simulate 50m corridor deviation to trigger automatic re-routing"
          >
            Simulate Deviation
          </button>

          <button
            onClick={handleTriggerSOSClick}
            className="rounded-xl bg-red-600 py-2 px-3.5 text-xs font-black text-white hover:bg-red-700 transition shadow flex items-center gap-1"
          >
            <span>{"\u{1F6A8}"}</span> SOS
          </button>

          <button
            onClick={handleEndTrip}
            className="rounded-xl bg-gray-900 py-2 px-3 text-xs font-bold text-white hover:bg-gray-800 transition"
          >
            End Trip
          </button>
        </div>
      </div>

      {/* SOS Confirmation Modal */}
      {showSOSConfirm && (
        <div className="rounded-2xl bg-red-950 text-white p-4 shadow-2xl border-2 border-red-500 animate-in fade-in zoom-in duration-150">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">{"\u{1F6A8}"}</span>
            <h3 className="font-extrabold text-sm uppercase tracking-wide">
              Confirm Emergency SOS Activation
            </h3>
          </div>
          <p className="text-xs text-red-200 mb-3 leading-relaxed">
            This will freeze your live location, pinpoint the nearest Chennai police station, alert your trusted contacts with a live tracking link, and inject an immediate emergency safety penalty on this road.
          </p>
          <input
            type="text"
            value={sosNotes}
            onChange={(e) => setSosNotes(e.target.value)}
            placeholder="Optional note (e.g., Suspicious person, broken lights)..."
            className="w-full text-xs bg-red-900/60 border border-red-700 rounded-lg p-2 text-white placeholder-red-300 mb-3 focus:outline-none"
          />
          <div className="flex space-x-2">
            <button
              onClick={handleConfirmTriggerSOS}
              disabled={sosTriggering}
              className="flex-1 bg-red-600 hover:bg-red-500 text-white font-bold py-2 px-3 rounded-lg text-xs shadow transition disabled:opacity-50"
            >
              {sosTriggering ? "Activating SOS..." : "\u{1F6A8} CONFIRM SOS NOW"}
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

      {/* Comprehensive Active SOS Emergency Card */}
      {activeSOS && (
        <div className="rounded-2xl bg-red-900 text-white p-4 shadow-2xl border-2 border-red-400 space-y-3">
          {/* Header */}
          <div className="flex items-center justify-between">
            <span className="font-extrabold text-xs uppercase tracking-wider bg-red-600 px-2.5 py-1 rounded-full animate-pulse flex items-center gap-1">
              <span>{"\u{1F6A8}"}</span> SOS ACTIVE (#{String(activeSOS.sos_id).slice(0, 8)})
            </span>
            <span className="text-xs text-red-200 font-medium">
              Road: {activeSOS.road_name || "Chennai Monitored Corridor"}
            </span>
          </div>

          {/* Nearest Police Help with 1-Tap Escape Button */}
          {activeSOS.nearest_police_station && (
            <div className="bg-red-950/90 p-3 rounded-xl border border-red-700 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-red-300 font-semibold uppercase tracking-wider text-[10px]">
                  Nearest Police Station
                </span>
                <span className="bg-red-800/80 px-2 py-0.5 rounded text-[10px] font-bold text-red-100">
                  {activeSOS.nearest_police_station.distance_km} km away
                </span>
              </div>
              <div className="font-bold text-white text-sm mt-1">
                {"\u{1F693} " + activeSOS.nearest_police_station.name}
              </div>
              <div className="text-red-200 text-[11px] mt-0.5">
                Line: <strong>{activeSOS.nearest_police_station.phone || "112 / 044-23452359"}</strong>
              </div>
              <button
                onClick={handleEscapeToPoliceStation}
                className="mt-2 w-full bg-red-700 hover:bg-red-600 text-white font-extrabold py-1.5 px-3 rounded-lg text-xs flex items-center justify-center gap-1.5 shadow transition"
              >
                <span>{"\u{1F3C3}"}</span> Escape / Navigate to {activeSOS.nearest_police_station.name.split(" ")[0]} Police Station
              </button>
            </div>
          )}

          {/* Dedicated Emergency Helplines (Chennai / TN / India) */}
          <div className="grid grid-cols-3 gap-1.5 text-center text-xs">
            <a
              href="tel:112"
              className="bg-white text-red-900 font-black py-2 px-1 rounded-xl shadow hover:bg-red-50 transition flex items-center justify-center gap-1"
            >
              <span>{"\u{1F4DE}"}</span> 112 Police
            </a>
            <a
              href="tel:1091"
              className="bg-pink-100 text-pink-950 font-black py-2 px-1 rounded-xl shadow hover:bg-pink-200 transition flex items-center justify-center gap-1"
              title="Tamil Nadu 24/7 Dedicated Women Helpline"
            >
              <span>{"\u{1F6E1}\u{FE0F}"}</span> 1091 Women
            </a>
            <a
              href="tel:108"
              className="bg-amber-100 text-amber-950 font-black py-2 px-1 rounded-xl shadow hover:bg-amber-200 transition flex items-center justify-center gap-1"
              title="Emergency Ambulance & Medical Services"
            >
              <span>{"\u{1F691}"}</span> 108 Medic
            </a>
          </div>

          {/* Trusted Contacts Action List */}
          {activeSOS.notified_contacts && activeSOS.notified_contacts.length > 0 ? (
            <div className="bg-red-950/70 p-3 rounded-xl border border-red-800 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-extrabold uppercase text-[10px] text-red-300 tracking-wider">
                  Trusted Emergency Contacts ({activeSOS.notified_contacts.length})
                </span>
                <button
                  onClick={handleBroadcastAllSMS}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-2 py-0.5 rounded text-[10px] font-extrabold shadow flex items-center gap-1"
                  title="Send direct SMS to all contacts at once"
                >
                  <span>{"\u{1F4E2}"}</span> Broadcast All (SMS)
                </button>
              </div>

              {activeSOS.notified_contacts.map((c: any, idx: number) => (
                <div
                  key={idx}
                  className="flex items-center justify-between bg-red-900/60 p-2 rounded-lg border border-red-800/80"
                >
                  <div className="min-w-0 pr-2">
                    <div className="font-bold text-white text-xs truncate">
                      {"\u{1F464} " + c.contact_name}
                    </div>
                    <div className="text-[11px] text-red-200">
                      {"\u{1F4DE} " + c.phone_number}
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => handleSendWhatsApp(c.phone_number)}
                      className="bg-emerald-700 hover:bg-emerald-600 text-white px-2 py-1 rounded-md text-[10px] font-bold shadow flex items-center gap-1"
                      title="Send WhatsApp emergency location alert"
                    >
                      <span className="text-emerald-400 font-bold mr-1">{"\u{25CF}"}</span> WhatsApp
                    </button>
                    <button
                      onClick={() => handleSendSMS(c.phone_number)}
                      className="bg-blue-700 hover:bg-blue-600 text-white px-2 py-1 rounded-md text-[10px] font-bold shadow flex items-center gap-1"
                      title="Send SMS text alert"
                    >
                      <span>{"\u{1F4AC}"}</span> SMS
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-2.5 rounded-lg bg-amber-950/60 border border-amber-700/60 text-xs text-amber-200">
              No trusted contacts registered yet. Add them in {"\u{1F6E1}\u{FE0F}"} Profile & Contacts.
            </div>
          )}

          {/* Defense Tools: Siren & Live Tracking Link */}
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={toggleSiren}
              className={`font-black py-2 px-3 rounded-xl text-xs transition flex items-center justify-center gap-1.5 shadow ${
                isSirenActive
                  ? "bg-amber-400 text-black animate-pulse border-2 border-white"
                  : "bg-red-800 hover:bg-red-700 text-white border border-red-600"
              }`}
            >
              <span>{isSirenActive ? "\u{1F507}" : "\u{1F50A}"}</span>
              <span>{isSirenActive ? "STOP SIREN ALARM" : "SOUND LOUD SIREN"}</span>
            </button>

            <button
              onClick={handleShareLiveLink}
              className="bg-red-700 hover:bg-red-600 text-white font-bold py-2 px-3 rounded-xl text-xs transition flex items-center justify-center gap-1.5 shadow"
            >
              <span>{"\u{1F517}"}</span> Open & Copy Live Link
            </button>
          </div>

          {/* Resolution & Safety Verdict Actions */}
          <div className="pt-1 border-t border-red-800 grid grid-cols-3 gap-1.5">
            <button
              onClick={() => handleResolveSOS("resolved")}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-black py-2.5 px-2 rounded-xl text-[11px] text-center shadow transition flex items-center justify-center gap-1"
              title="Situation safe, clear alert and resume trip"
            >
              <span>{"\u{2705}"}</span> Mark Safe
            </button>

            <button
              onClick={handleMarkRouteUnsafe}
              className="bg-amber-600 hover:bg-amber-500 text-white font-black py-2.5 px-2 rounded-xl text-[11px] text-center shadow transition flex items-center justify-center gap-1"
              title="Report this road as unsafe and automatically re-route around it"
            >
              <span>{"\u{26A0}\u{FE0F}"}</span> Mark Unsafe & Divert
            </button>

            <button
              onClick={() => handleResolveSOS("cancelled")}
              className="bg-gray-800 hover:bg-gray-700 text-gray-200 font-bold py-2.5 px-2 rounded-xl text-[11px] text-center shadow transition flex items-center justify-center gap-1"
              title="Cancel false alarm and resume navigation"
            >
              <span>{"\u{2715}"}</span> False Alarm
            </button>
          </div>
        </div>
      )}

      {sosBannerMessage && !activeSOS && (
        <div className="bg-emerald-800 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow border border-emerald-500 animate-in fade-in duration-200">
          {sosBannerMessage}
        </div>
      )}
    </div>
  );
}
