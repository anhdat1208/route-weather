import type { LatLng, TravelMode } from "./routeWeather"

export type IntelligenceStatus = "ok" | "partial" | "unavailable"
export type RiskBand = "low" | "moderate" | "high" | "severe"

export interface RouteIntelligenceRequest {
  origin: LatLng
  destination: LatLng
  departure_time: string
  travel_mode: TravelMode
  origin_label?: string | null
  destination_label?: string | null
  geocode_route_points?: boolean
  include_fusion?: boolean
  include_traffic?: boolean
  include_nowcast?: boolean
}

export interface SegmentWeatherIntel {
  rain_probability_pct: number | null
  rain_intensity_mm: number | null
  rain_status: string | null
  condition: string | null
  confidence: number
  source: string
  prediction_horizon_minutes: number | null
  nowcast_used: boolean
  data_quality: string | null
}

export interface SegmentTrafficIntel {
  predicted_speed_kmh: number | null
  predicted_congestion: string | null
  current_congestion: string | null
  speed_reduction_pct: number | null
  confidence: number
  weather_impact_level: string | null
  weather_adjusted_speed_kmh: number | null
  source: string
  stale: boolean
}

export interface SegmentRiskIntel {
  weather_risk_score: number
  weather_risk_level: RiskBand
  traffic_risk_score: number
  traffic_risk_level: RiskBand
  travel_risk_score: number
  travel_risk_level: RiskBand
  confidence: number
  contributors: string[]
}

export interface RouteIntelligenceSegment {
  id: string
  index: number
  coordinates: LatLng[]
  distance_m: number
  travel_time_seconds: number
  arrival_time: string
  label: string | null
  weather: SegmentWeatherIntel
  traffic: SegmentTrafficIntel | null
  risk: SegmentRiskIntel
}

export interface RouteIntelSummary {
  risk_level: RiskBand
  score: number
  worst_segment_id: string | null
  worst_segment_index: number | null
  worst_segment_label: string | null
  weather_status: string
  traffic_status: string | null
  confidence: number
  eta_minutes: number
  distance_km: number
  weather_summary: string
  traffic_summary: string
  worst_condition: string | null
}

export interface RouteIntelExplainability {
  overall_risk_level: RiskBand
  score: number
  main_contributors: string[]
  weather: string[]
  traffic: string[]
  worst_segment_id: string | null
  confidence: number
}

export interface RouteIntelRecommendation {
  message: string
  details: string[]
}

export interface DepartureAlternative {
  departure_time: string
  offset_minutes: number
  risk_level: RiskBand
  score: number
}

export interface RouteIntelligenceResponse {
  generated_at: string
  status: IntelligenceStatus
  route: {
    distance_km: number
    duration_minutes: number
    distance_m?: number
    duration_seconds?: number
  }
  summary: RouteIntelSummary
  segments: RouteIntelligenceSegment[]
  recommendation: RouteIntelRecommendation
  explainability: RouteIntelExplainability
  departure_alternatives: DepartureAlternative[]
}

export interface RouteIntelligenceCompareResponse {
  baseline: RouteIntelligenceResponse
  alternatives: DepartureAlternative[]
}
