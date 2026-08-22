export type LatLng = { lat: number; lng: number }
export type GeocodeResult = { label: string; point: LatLng; approximate?: boolean }
export type TravelMode = "motorbike" | "walking"
export type WeatherStatus = "ok" | "partial" | "unavailable"
export type RiskLevel = "very_low" | "low" | "moderate" | "high" | "very_high"

export type WeatherSnapshot = {
  time: string
  weather_code?: number | null
  condition?: string | null
  temperature_c?: number | null
  apparent_temperature_c?: number | null
  precipitation_probability_pct?: number | null
  precipitation_mm?: number | null
  wind_speed_kmh?: number | null
  wind_direction_deg?: number | null
  humidity_percent?: number | null
  visibility_km?: number | null
}

export type RouteWeatherTimelinePoint = {
  index: number
  arrival_time: string
  distance_km: number
  label: string | null
  weather: WeatherSnapshot | null
  precipitation_probability_pct: number | null
  precipitation_label: { label: string; probability_pct: number } | null
}

export type RouteWeatherSegment = {
  index: number
  coordinates: LatLng[]
  arrival_time: string
  start_distance_km: number
  end_distance_km: number
  risk_score: number
  risk_level: RiskLevel
  weather: WeatherSnapshot | null
  label: string | null
}

export type RouteWeatherResponse = {
  route: { distance_km: number; duration_minutes: number }
  weather_status: WeatherStatus
  risk: { score: number; level: RiskLevel; summary: string; worst_segment_index: number | null }
  segments: RouteWeatherSegment[]
  timeline: RouteWeatherTimelinePoint[]
  recommendation: {
    message: string
    alternatives: Array<{ departure_time: string; risk_score: number; level: RiskLevel }>
  }
}

export type LoadingPhase = "idle" | "routing" | "weather" | "done"
