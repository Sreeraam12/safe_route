"use client";

import { useEffect, useState } from "react";
import { getPreferences, updatePreferences, getTwinState } from "../../services/routeApi";
import type { PersonalPreferences, PersonalTwinState } from "../../types/route";

interface PreferencesModalProps {
  onClose: () => void;
}

export default function PreferencesModal({ onClose }: PreferencesModalProps) {
  const [prefs, setPrefs] = useState<PersonalPreferences | null>(null);
  const [twin, setTwin] = useState<PersonalTwinState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const [p, t] = await Promise.all([getPreferences(), getTwinState()]);
        setPrefs(p);
        setTwin(t);
      } catch (err) {
        console.error("Error loading preferences:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSave = async () => {
    if (!prefs) return;
    setSaving(true);
    try {
      await updatePreferences(prefs);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error("Save error:", err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b pb-3">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Safety Preferences & Digital Twin</h2>
            <p className="text-xs text-gray-500">Configure your safety priorities</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-800 text-lg">✕</button>
        </div>

        {loading ? (
          <p className="text-xs text-gray-500 py-6 text-center">Loading preferences...</p>
        ) : prefs ? (
          <div className="space-y-4 text-xs">
            {/* Learned Twin Overview */}
            {twin && (
              <div className="rounded-xl bg-purple-50 p-3.5 border border-purple-100 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-purple-900 flex items-center gap-1.5">
                    <span>🧬</span> Personal Digital Twin
                  </span>
                  <span className="rounded-full bg-purple-200 px-2 py-0.5 text-[10px] font-bold text-purple-800">
                    Confidence: {(twin.model_confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-[11px] text-purple-700">
                  Learned from your trip selections and feedback. Governs how routes are personalized.
                </p>
                <div className="grid grid-cols-3 gap-1.5 pt-1 text-[10px] text-purple-800">
                  <div>💡 Lighting: {(twin.lighting_weight * 100).toFixed(0)}%</div>
                  <div>🛡️ Crime: {(twin.crime_weight * 100).toFixed(0)}%</div>
                  <div>🌙 Night: {(twin.night_weight * 100).toFixed(0)}%</div>
                </div>
              </div>
            )}

            {/* Sliders */}
            <div className="space-y-3">
              <div>
                <div className="flex justify-between font-semibold text-gray-700">
                  <span>Street Lighting Priority</span>
                  <span>{Math.round(prefs.lighting_preference * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={prefs.lighting_preference}
                  onChange={(e) => setPrefs({ ...prefs, lighting_preference: Number(e.target.value) })}
                  className="w-full accent-blue-600 mt-1"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-gray-700">
                  <span>Night Safety Sensitivity</span>
                  <span>{Math.round(prefs.night_safety_weight * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={prefs.night_safety_weight}
                  onChange={(e) => setPrefs({ ...prefs, night_safety_weight: Number(e.target.value) })}
                  className="w-full accent-blue-600 mt-1"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-gray-700">
                  <span>Isolation Aversion</span>
                  <span>{Math.round(prefs.isolation_aversion * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={prefs.isolation_aversion}
                  onChange={(e) => setPrefs({ ...prefs, isolation_aversion: Number(e.target.value) })}
                  className="w-full accent-blue-600 mt-1"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-gray-700">
                  <span>Crime Area Sensitivity</span>
                  <span>{Math.round(prefs.crime_sensitivity * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={prefs.crime_sensitivity}
                  onChange={(e) => setPrefs({ ...prefs, crime_sensitivity: Number(e.target.value) })}
                  className="w-full accent-blue-600 mt-1"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-gray-700">
                  <span>Max Detour for Safety</span>
                  <span>{Math.round(prefs.detour_tolerance * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.5"
                  step="0.05"
                  value={prefs.detour_tolerance}
                  onChange={(e) => setPrefs({ ...prefs, detour_tolerance: Number(e.target.value) })}
                  className="w-full accent-blue-600 mt-1"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t">
              {saved && <span className="text-green-600 font-semibold">✓ Preferences saved</span>}
              <div className="flex gap-2 ml-auto">
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-xl px-4 py-2 font-semibold text-gray-500 hover:bg-gray-100"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={saving}
                  className="rounded-xl bg-black px-5 py-2 font-semibold text-white shadow hover:bg-gray-800 disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save Preferences"}
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

