export interface RouteInstruction {
  step: number;
  instruction: string;
  distance_m: number;
  distance: string;
}

export interface RouteResult {
  rank: number;
  route_index: number;
  distance_km: number;
  final_risk: number;
  safety_score: number;
  personalized_risk?: number;
  personalized_safety_score?: number;
  personal_adjustment?: number;
  hybrid_risk: number;
  hybrid_safety: number;
  base_hybrid_risk?: number;
  time_risk?: number;
  time_period?: string;
  traffic_risk: number;
  traffic_safety: number;
  traffic_coverage_pct: number;
  traffic_matched_segments: number;
  traffic_total_segments: number;
  geometry: [number, number][];
  road_names: string[];
  instructions: RouteInstruction[];
}

export interface RouteSearchResponse {
  source: {
    name: string;
    latitude: number;
    longitude: number;
  };

  destination: {
    name: string;
    latitude: number;
    longitude: number;
  };

  source_node: number;
  destination_node: number;
  route_count: number;
  routes: RouteResult[];
}

export interface UserProfile {
  id: number;
  email: string;
  name: string;
  created_at: string;
}

export interface PersonalPreferences {
  user_id: number;
  lighting_preference: number;
  crowd_preference: number;
  isolation_aversion: number;
  cctv_preference: number;
  police_proximity_preference: number;
  main_road_preference: number;
  crime_sensitivity: number;
  traffic_tolerance: number;
  distance_priority: number;
  time_priority: number;
  detour_tolerance: number;
  night_safety_weight: number;
  weather_sensitivity: number;
  updated_at: string;
}

export interface PersonalTwinState {
  user_id: number;
  timestamp: string;
  lighting_weight: number;
  crime_weight: number;
  isolation_weight: number;
  crowd_weight: number;
  traffic_weight: number;
  distance_weight: number;
  time_weight: number;
  night_weight: number;
  weather_weight: number;
  detour_tolerance: number;
  model_confidence: number;
}

export interface NavigationStatus {
  trip_id: string;
  current_instruction: string;
  next_instruction?: string | null;
  step_number: number;
  total_steps: number;
  distance_to_turn_m: number;
  distance_to_turn_formatted: string;
  remaining_distance_km: number;
  eta_minutes: number;
  off_route: boolean;
  consecutive_deviations: number;
  rerouting: boolean;
  is_at_destination: boolean;
  new_route?: RouteResult | null;
}

export interface TripFeedbackItem {
  id: string;
  safety_rating: number;
  comfort_rating: number;
  lighting_rating: number;
  crowd_rating: number;
  felt_unsafe: boolean;
  incident_reported: boolean;
  feedback_text?: string;
  created_at: string;
}

export interface TripHistoryItem {
  id: string;
  user_id?: string;
  trip_datetime?: string;
  travel_date: string;
  travel_time: string;
  source_zone: string;
  destination_zone: string;
  source_lat: number;
  source_lon: number;
  dest_lat: number;
  dest_lon: number;
  travel_mode: string;
  trip_intent?: string;
  selected_route_id: number;
  selected_distance_km: number;
  selected_duration_min?: number;
  selected_safety_score: number;
  actual_distance_km?: number;
  actual_duration_min?: number;
  route_deviation_pct?: number;
  completed: boolean;
  feedback?: TripFeedbackItem | null;
  created_at: string;
}