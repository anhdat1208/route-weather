import type { LatLng, TravelMode, WeatherSnapshot } from "~/types/routeWeather"

export type DataQuality = "GOOD" | "STALE" | "MISSING" | "CONFLICTING" | "UNKNOWN"

export interface ObservationMetadata {
  source: string
  observed_at: string
  received_at?: string | null
  age_seconds?: number | null
}

export interface SourceQuality {
  forecast: DataQuality
  radar: DataQuality
  satellite: DataQuality
  rain_cell: DataQuality
  conflicts: string[]
}

export interface FusedRainCellSummary {
  count: number
  nearest_distance_km?: number | null
  max_intensity_mean?: number | null
  corridor_overlap?: number | null
}

export interface SegmentNowcastFeatures {
  precip_probability_pct?: number | null
  precip_mm?: number | null
  rain_cell_count: number
  nearest_rain_cell_km?: number | null
  rain_cell_max_intensity?: number | null
  rain_cell_corridor_overlap?: number | null
  radar_age_seconds?: number | null
  satellite_age_seconds?: number | null
  radar_satellite_delta_seconds?: number | null
  radar_available: boolean
  satellite_available: boolean
  precip_evidence: boolean
}

export interface FusedSegmentState {
  segment_index: number
  arrival_time: string
  segment_start: LatLng
  segment_end: LatLng
  forecast?: WeatherSnapshot | null
  forecast_meta?: ObservationMetadata | null
  radar_meta?: ObservationMetadata | null
  satellite_meta?: ObservationMetadata | null
  rain_cell_meta?: ObservationMetadata | null
  rain_cell?: FusedRainCellSummary | null
  data_quality: SourceQuality
  features: SegmentNowcastFeatures
  confidence: number
}

export interface WeatherFusionResponse {
  observed_at: string
  route_distance_km: number
  route_duration_minutes: number
  segments: FusedSegmentState[]
  source_versions: Record<string, string>
}

export interface WeatherFusionRequest {
  origin: LatLng
  destination: LatLng
  departure_time: string
  travel_mode: TravelMode
  include_rain_cells?: boolean
}
