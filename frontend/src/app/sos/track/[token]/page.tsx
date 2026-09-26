"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SOSTrackPage() {
  const params = useParams();
  const token = params?.token as string;
  const [sosData, setSosData] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/sos/track/${token}`);
        if (!res.ok) throw new Error("SOS session not found");
        const data = await res.json();
        setSosData(data);
      } catch (e: any) {
        setError(e.message);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [token]);

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-6">
        <div className="bg-red-950/60 border border-red-700 p-6 rounded-2xl max-w-md w-full text-center">
          <h1 className="text-xl font-bold text-red-300">SOS Tracking Link</h1>
          <p className="text-sm text-red-200 mt-2">{error}</p>
          <a href="/" className="mt-4 inline-block bg-red-600 px-4 py-2 rounded-xl text-xs font-bold">
            Return to SafeRoute Map
          </a>
        </div>
      </div>
    );
  }

  if (!sosData) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center">
        <div className="text-sm font-bold animate-pulse text-red-400">
          Loading Live Emergency SOS Telemetry...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6 flex flex-col items-center justify-center">
      <div className="max-w-lg w-full bg-red-950/80 border-2 border-red-500 rounded-3xl p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between">
          <span className="bg-red-600 text-white text-xs font-extrabold px-3 py-1 rounded-full uppercase animate-pulse">
            🚨 LIVE SOS EMERGENCY ({sosData.status})
          </span>
          <span className="text-xs text-red-200">ID: #{String(sosData.sos_id).slice(0, 8)}</span>
        </div>

        <div>
          <div className="text-xs text-red-300 uppercase font-semibold">Current Snapped Road Corridor</div>
          <div className="text-xl font-extrabold text-white mt-0.5">{sosData.road_name || "Chennai Arterial Road"}</div>
          <div className="text-xs text-red-200 mt-1">
            Live GPS Coordinates: <strong>{Number(sosData.latest_lat).toFixed(5)}, {Number(sosData.latest_lon).toFixed(5)}</strong>
          </div>
        </div>

        {sosData.nearest_police_station && (
          <div className="bg-black/40 p-4 rounded-2xl border border-red-700/80">
            <div className="text-xs font-bold text-red-300 uppercase">Nearest Police Assistance</div>
            <div className="text-base font-extrabold text-white mt-1">
              🚓 {sosData.nearest_police_station.name} ({sosData.nearest_police_station.distance_km} km away)
            </div>
            <div className="text-xs text-red-200 mt-1">
              Emergency Dispatch: <strong>{sosData.nearest_police_station.phone}</strong>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 pt-2">
          <a
            href={`https://www.google.com/maps?q=${sosData.latest_lat},${sosData.latest_lon}`}
            target="_blank"
            rel="noreferrer"
            className="bg-white text-red-900 font-extrabold py-3 px-4 rounded-xl text-xs text-center shadow hover:bg-red-50 transition"
          >
            📍 Open in Google Maps
          </a>
          <a
            href="tel:112"
            className="bg-red-600 hover:bg-red-500 text-white font-extrabold py-3 px-4 rounded-xl text-xs text-center shadow transition"
          >
            📞 Call 112 Police
          </a>
        </div>

        <div className="pt-2 text-center">
          <a href="/" className="text-xs text-red-300 underline hover:text-white">
            ← Back to SafeRoute Navigation Map
          </a>
        </div>
      </div>
    </div>
  );
}
