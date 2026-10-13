import type {
  RouteSearchResponse,
  UserProfile,
  PersonalPreferences,
  PersonalTwinState,
  NavigationStatus,
  RouteResult,
} from "../types/route";

export function getApiUrl(): string {
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") {
      return "http://localhost:8000";
    }
    if (host) {
      return `http://${host}:8000`;
    }
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

function getAuthHeader(): Record<string, string> {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("saferoute_token");
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
  }
  return {};
}

export async function searchRoutes(
  source: string,
  destination: string,
  travelDate?: string,
  travelTime?: string
): Promise<RouteSearchResponse> {
  const payload: Record<string, string> = {
    source,
    destination,
  };

  if (travelDate) {
    payload.travel_date = travelDate;
  }
  if (travelTime) {
    payload.travel_time = travelTime;
  }

  let response: Response;
  try {
    response = await fetch(`${getApiUrl()}/api/routes/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new Error("Unable to connect to SafeRoute server. Please ensure backend is running.");
  }

  if (!response.ok) {
    let message = "Failed to find routes.";
    try {
      const error = await response.json();
      if (error?.detail) {
        message = error.detail;
      }
    } catch {
      // Keep default error message
    }
    throw new Error(message);
  }

  return response.json();
}

// -------------------------------------------------------------
// AUTHENTICATION APIs
// -------------------------------------------------------------

export async function registerUser(email: string, password: string, name: string) {
  let response: Response;
  try {
    response = await fetch(`${getApiUrl()}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name }),
    });
  } catch {
    throw new Error("Unable to connect to SafeRoute backend server on port 8000.");
  }

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Registration failed. Please check your details.");
  }

  const data = await response.json();
  if (typeof window !== "undefined") {
    localStorage.setItem("saferoute_token", data.access_token);
  }
  return data;
}

export async function loginUser(email: string, password: string) {
  let response: Response;
  try {
    response = await fetch(`${getApiUrl()}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    throw new Error("Unable to connect to SafeRoute backend server on port 8000.");
  }

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    if (response.status === 401 || err.detail?.toLowerCase().includes("incorrect")) {
      throw new Error("Invalid credentials");
    }
    throw new Error(err.detail || "Invalid credentials");
  }

  const data = await response.json();
  if (typeof window !== "undefined") {
    localStorage.setItem("saferoute_token", data.access_token);
  }
  return data;
}

export async function getMe(): Promise<UserProfile> {
  const response = await fetch(`${getApiUrl()}/api/auth/me`, {
    headers: { ...getAuthHeader() },
  });
  if (!response.ok) throw new Error("Not authenticated");
  return response.json();
}

// -------------------------------------------------------------
// PREFERENCES & TWIN APIs
// -------------------------------------------------------------

export async function getPreferences(): Promise<PersonalPreferences> {
  const response = await fetch(`${getApiUrl()}/api/users/me/preferences`, {
    headers: { ...getAuthHeader() },
  });
  if (!response.ok) throw new Error("Failed to load preferences");
  return response.json();
}

export async function updatePreferences(updates: Partial<PersonalPreferences>): Promise<PersonalPreferences> {
  const response = await fetch(`${getApiUrl()}/api/users/me/preferences`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify(updates),
  });
  if (!response.ok) throw new Error("Failed to update preferences");
  return response.json();
}

export async function getTwinState(): Promise<PersonalTwinState> {
  const response = await fetch(`${getApiUrl()}/api/users/me/twin`, {
    headers: { ...getAuthHeader() },
  });
  if (!response.ok) throw new Error("Failed to load twin state");
  return response.json();
}

// -------------------------------------------------------------
// TRIPS & FEEDBACK APIs
// -------------------------------------------------------------

export async function createTrip(payload: any) {
  const response = await fetch(`${getApiUrl()}/api/trips`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("Failed to create trip");
  return response.json();
}

export async function submitTripFeedback(
  tripId: string,
  feedback: {
    safety_rating: number;
    comfort_rating?: number;
    lighting_rating?: number;
    crowd_rating?: number;
    navigation_rating?: number;
    felt_unsafe?: boolean;
    incident_reported?: boolean;
    incident_type?: string;
    feedback_text?: string;
  }
) {
  const response = await fetch(`${getApiUrl()}/api/trips/${tripId}/feedback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify(feedback),
  });
  if (!response.ok) throw new Error("Failed to submit feedback");
  return response.json();
}

export async function completeTrip(tripId: string) {
  try {
    const response = await fetch(`${getApiUrl()}/api/trips/${tripId}/complete`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function getTripHistory(): Promise<import("../types/route").TripHistoryItem[]> {
  const response = await fetch(`${getApiUrl()}/api/trips/history`, {
    headers: {
      ...getAuthHeader(),
    },
  });
  if (!response.ok) throw new Error("Failed to fetch trip history");
  return response.json();
}

// -------------------------------------------------------------
// NAVIGATION APIs
// -------------------------------------------------------------

export async function startNavigation(payload: {
  trip_id: string;
  selected_route_index: number;
  geometry: [number, number][];
  instructions: any[];
  destination_lat: number;
  dest_lon: number;
}) {
  const response = await fetch(`${getApiUrl()}/api/navigation/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}

export async function updateGPSLocation(payload: {
  trip_id: string;
  latitude: number;
  longitude: number;
  speed?: number;
  heading?: number;
}): Promise<NavigationStatus> {
  const response = await fetch(`${getApiUrl()}/api/navigation/update`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("GPS update failed");
  return response.json();
}

export async function endNavigation(tripId: string) {
  const response = await fetch(`${getApiUrl()}/api/navigation/end?trip_id=${tripId}`, {
    method: "POST",
  });
  return response.json();
}
export async function manualReroute(payload: {
  trip_id: string;
  current_lat: number;
  current_lon: number;
  destination_lat: number;
  dest_lon: number;
}) {
  const response = await fetch(`${getApiUrl()}/api/navigation/reroute`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("Reroute failed");
  return response.json();
}

export async function fetchActiveAlertsForMe() {
  const token = typeof window !== "undefined" ? (localStorage.getItem("saferoute_token") || localStorage.getItem("token")) : null;
  if (!token) return { alerts: [] };
  try {
    const response = await fetch(`${getApiUrl()}/api/sos/active-alerts-for-me`, {
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!response.ok) return { alerts: [] };
    return response.json();
  } catch {
    return { alerts: [] };
  }
}

export async function getSegmentMemory() {
  try {
    const response = await fetch(`${getApiUrl()}/api/users/me/segment-memory`, {
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}
