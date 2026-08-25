import type { LatLng } from "~/types/routeWeather"

export type TrafficHorizon = 5 | 10 | 15 | 30
export type TrafficSelectedHorizon = 0 | TrafficHorizon
export type TrafficStatus = "ok" | "partial" | "unavailable"
export type NowcastEmbedStatus = "ok" | "partial" | "unavailable" | "skipped"
export type CongestionLevel = "free" | "slow" | "moderate" | "heavy" | "severe"
export type WeatherImpactLevel = "none" | "low" | "moderate" | "high"

export type TrafficModelInfo = {
  name: string
  version: string
}

export type TrafficState = {
  current_speed_kmh: number | null
  free_flow_speed_kmh: number | null
  congestion_level: CongestionLevel | null
  relative_speed: number | null
  timestamp: string
  source: string
  stale: boolean
}

export type RoadSegment = {
  id: string
  geometry: LatLng[]
  road_type?: string | null
  name?: string | null
  traffic: TrafficState | null
}

export type SpeedCongestionPair = {
  speed_kmh: number | null
  congestion: CongestionLevel | null
  speed_delta_pct?: number | null
}

export type WeatherImpactInfo = {
  speed_delta_pct: number
  level: WeatherImpactLevel
  rain_probability: number | null
  rain_intensity: number | null
  reasons: string[]
}

export type TrafficPrediction = {
  road_segment_id: string
  forecast_minutes: TrafficHorizon
  predicted_speed_kmh: number | null
  predicted_congestion: CongestionLevel | null
  confidence: number
  base_prediction: SpeedCongestionPair
  weather_impact: WeatherImpactInfo
  weather_adjusted: SpeedCongestionPair
  model: TrafficModelInfo
}

export type TrafficPredictionResponse = {
  generated_at: string
  status: TrafficStatus
  model: TrafficModelInfo
  horizons: number[]
  segments: RoadSegment[]
  predictions: TrafficPrediction[]
  nowcast_status: NowcastEmbedStatus
  message?: string | null
}

export type TrafficPredictRequest = {
  geometry: LatLng[]
  buffer_km?: number | null
}
