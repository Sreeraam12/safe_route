"use client";

import { useState } from "react";
import { submitTripFeedback } from "../../services/routeApi";

interface TripFeedbackModalProps {
  tripId: string;
  onClose: () => void;
}

export default function TripFeedbackModal({
  tripId,
  onClose,
}: TripFeedbackModalProps) {
  const [safetyRating, setSafetyRating] = useState(4);
  const [feltUnsafe, setFeltUnsafe] = useState(false);
  const [lightingRating, setLightingRating] = useState(3);
  const [comfortRating, setComfortRating] = useState(4);
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
        feedback_text: feedbackText.trim() || undefined,
      });
      setSubmitted(true);
    } catch (err) {
      console.error("Feedback error:", err);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        {!submitted ? (
          <div className="space-y-4">
            <div>
              <span className="text-2xl">🏁</span>
              <h2 className="mt-1 text-xl font-bold text-gray-900">
                Trip Complete
              </h2>
              <p className="text-xs text-gray-500">
                Your feedback trains your Personal Digital Twin to recommend safer routes in the future.
              </p>
            </div>

            {/* Overall Safety Rating */}
            <div>
              <label className="block text-xs font-semibold text-gray-700">
                How safe did you feel on this route?
              </label>
              <div className="mt-1.5 flex gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setSafetyRating(star)}
                    className={`flex h-10 w-10 items-center justify-center rounded-xl text-lg transition ${
                      safetyRating >= star
                        ? "bg-amber-100 text-amber-600 scale-105"
                        : "bg-gray-100 text-gray-400 hover:bg-gray-200"
                    }`}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>

            {/* Unsafe Toggle */}
            <div className="flex items-center justify-between rounded-xl bg-gray-50 p-3">
              <div>
                <p className="text-xs font-semibold text-gray-800">Did you feel unsafe at any point?</p>
                <p className="text-[11px] text-gray-500">Adjusts sensitivity weights in your Twin</p>
              </div>
              <input
                type="checkbox"
                checked={feltUnsafe}
                onChange={(e) => setFeltUnsafe(e.target.checked)}
                className="h-5 w-5 rounded accent-red-600 cursor-pointer"
              />
            </div>

            {/* Lighting Rating */}
            <div>
              <div className="flex justify-between text-xs font-medium text-gray-600">
                <span>Street Lighting Quality</span>
                <span>{lightingRating} / 5</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                value={lightingRating}
                onChange={(e) => setLightingRating(Number(e.target.value))}
                className="mt-1 w-full accent-blue-600"
              />
            </div>

            {/* Comments */}
            <div>
              <label className="block text-xs font-semibold text-gray-700">
                Additional Comments (optional)
              </label>
              <textarea
                rows={2}
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="e.g. isolated stretch near railway bridge, good streetlamps"
                className="mt-1 w-full rounded-lg border border-gray-300 p-2.5 text-xs outline-none focus:border-gray-500"
              />
            </div>

            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 rounded-xl py-2.5 text-xs font-semibold text-gray-500 hover:bg-gray-100"
              >
                Skip
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="flex-1 rounded-xl bg-blue-600 py-2.5 text-xs font-semibold text-white shadow transition hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? "Submitting..." : "Submit Feedback"}
              </button>
            </div>
          </div>
        ) : (
          <div className="py-6 text-center space-y-3">
            <span className="text-4xl">✨</span>
            <h3 className="text-lg font-bold text-gray-900">Personal Twin Updated!</h3>
            <p className="text-xs text-gray-500">
              Your feedback has been incorporated into your Personal Digital Twin state. Model confidence and road memory updated.
            </p>
            <button
              onClick={onClose}
              className="mt-4 rounded-xl bg-black px-6 py-2.5 text-xs font-semibold text-white"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

