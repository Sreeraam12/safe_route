"use client";

import { useState } from "react";
import { submitTripFeedback } from "../../services/routeApi";

interface TripFeedbackModalProps {
  tripId: string;
  onClose: () => void;
  onFeedbackSubmitted?: () => void;
}

export default function TripFeedbackModal({
  tripId,
  onClose,
  onFeedbackSubmitted,
}: TripFeedbackModalProps) {
  const [safetyRating, setSafetyRating] = useState(4);
  const [feltUnsafe, setFeltUnsafe] = useState(false);
  const [lightingRating, setLightingRating] = useState(3);
  const [comfortRating, setComfortRating] = useState(4);
  const [crowdRating, setCrowdRating] = useState(4);
  const [navigationRating, setNavigationRating] = useState(5);
  const [feedbackText, setFeedbackText] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await submitTripFeedback(tripId, {
        safety_rating: safetyRating,
        felt_unsafe: feltUnsafe,
        lighting_rating: lightingRating,
        comfort_rating: comfortRating,
        crowd_rating: crowdRating,
        navigation_rating: navigationRating,
        feedback_text: feedbackText.trim() || undefined,
      });
      setSubmitted(true);
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }
    } catch (err) {
      console.error("Feedback error:", err);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md max-h-[92vh] overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl border border-gray-100">
        {!submitted ? (
          <div className="space-y-4">
            {/* Header */}
            <div>
              <div className="text-2xl mb-1">🏁</div>
              <h2 className="text-2xl font-bold tracking-tight text-gray-900">
                Trip Complete
              </h2>
              <p className="mt-1 text-xs text-gray-500 leading-relaxed">
                Your feedback trains your Personal Digital Twin to recommend safer routes in the future.
              </p>
            </div>

            {/* Overall Safety Rating (Stars) */}
            <div className="pt-1">
              <label className="block text-xs font-bold text-gray-800 mb-2">
                How safe did you feel on this route?
              </label>
              <div className="flex gap-2.5">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setSafetyRating(star)}
                    className={`flex h-11 w-11 items-center justify-center rounded-2xl text-xl font-bold transition duration-150 ${
                      safetyRating >= star
                        ? "bg-amber-100 text-amber-500 shadow-sm scale-105"
                        : "bg-gray-100 text-gray-400 hover:bg-gray-200"
                    }`}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>

            {/* Unsafe Toggle Box */}
            <div className="flex items-center justify-between rounded-2xl bg-gray-50/90 p-3.5 border border-gray-100">
              <div>
                <p className="text-xs font-bold text-gray-800">
                  Did you feel unsafe at any point?
                </p>
                <p className="text-[11px] text-gray-500 mt-0.5">
                  Adjusts sensitivity weights in your Twin
                </p>
              </div>
              <input
                type="checkbox"
                checked={feltUnsafe}
                onChange={(e) => setFeltUnsafe(e.target.checked)}
                className="h-5 w-5 rounded-md border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer accent-blue-600"
              />
            </div>

            {/* Street Lighting Quality */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-semibold text-gray-700">
                <span>Street Lighting Quality</span>
                <span className="text-blue-600 font-bold">{lightingRating} / 5</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={lightingRating}
                onChange={(e) => setLightingRating(Number(e.target.value))}
                className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-blue-600"
              />
            </div>

            {/* Road Comfort & Quality */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-semibold text-gray-700">
                <span>Road Comfort & Surface Quality</span>
                <span className="text-blue-600 font-bold">{comfortRating} / 5</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={comfortRating}
                onChange={(e) => setComfortRating(Number(e.target.value))}
                className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-blue-600"
              />
            </div>

            {/* Crowd & Bystander Activity */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-semibold text-gray-700">
                <span>Crowd & Activity Level</span>
                <span className="text-blue-600 font-bold">{crowdRating} / 5</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={crowdRating}
                onChange={(e) => setCrowdRating(Number(e.target.value))}
                className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-blue-600"
              />
            </div>

            {/* Navigation & Turn Accuracy */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-semibold text-gray-700">
                <span>Navigation & Guidance Accuracy</span>
                <span className="text-blue-600 font-bold">{navigationRating} / 5</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={navigationRating}
                onChange={(e) => setNavigationRating(Number(e.target.value))}
                className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-blue-600"
              />
            </div>

            {/* Comments */}
            <div>
              <label className="block text-xs font-bold text-gray-800 mb-1">
                Additional Comments (optional)
              </label>
              <textarea
                rows={2}
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="e.g. isolated stretch near railway bridge, good streetlamps"
                className="w-full rounded-xl border border-gray-200 p-2.5 text-xs text-gray-800 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition resize-none placeholder:text-gray-400"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 rounded-2xl py-3 text-xs font-bold text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition"
              >
                Skip
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="flex-[1.5] rounded-2xl bg-blue-600 py-3 text-xs font-bold text-white shadow-lg shadow-blue-500/25 transition hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? "Submitting..." : "Submit Feedback"}
              </button>
            </div>
          </div>
        ) : (
          <div className="py-6 text-center space-y-3">
            <span className="text-4xl">✨</span>
            <h3 className="text-xl font-bold text-gray-900">Personal Twin Updated!</h3>
            <p className="text-xs text-gray-500 max-w-xs mx-auto leading-relaxed">
              Your feedback has been incorporated into your Personal Digital Twin state. Model confidence, lighting weights, and road memory have been updated.
            </p>
            <div className="pt-2">
              <button
                onClick={onClose}
                className="w-full rounded-2xl bg-gray-900 px-6 py-3 text-xs font-bold text-white hover:bg-black transition shadow-md"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
