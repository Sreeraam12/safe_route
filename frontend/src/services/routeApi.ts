import type { RouteSearchResponse } from "../types/route";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export async function searchRoutes(
  source: string,
  destination: string
): Promise<RouteSearchResponse> {
  const response = await fetch(
    `${API_URL}/api/routes/search`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        source,
        destination,
      }),
    }
  );

  if (!response.ok) {
    let message = "Failed to find routes.";

    try {
      const error = await response.json();

      if (error?.detail) {
        message = error.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(message);
  }

  return response.json();
}