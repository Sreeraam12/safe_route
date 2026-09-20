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
  hybrid_risk: number;
  hybrid_safety: number;
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