import type { LatLng } from "~/types/routeWeather"
import type { CellBounds } from "~/types/rainCell"

export type NowcastHorizon = 5 | 10 | 15 | 30 | 60
export type NowcastSelectedHorizon = 0 | NowcastHorizon
export type NowcastStatus = "ok" | "partial" | "unavailable"

export type NowcastModelInfo = {
  name: string
  version: string
}

export type PredictedCellMotion = {
  speed_kmh?: number | null
  bearing_degrees?: number | null
}

export type PredictedRainCell = {
  cell_id: string
  forecast_minutes: NowcastHorizon
  kind: "predicted"
  centroid: LatLng
  bounds?: CellBounds | null
  rain_probability: number | null
  rain_intensity: number | null
  confidence: number
  motion?: PredictedCellMotion | null
  source: string
}

export type NowcastPredictionResponse = {
  generated_at: string
  status: NowcastStatus
  model: NowcastModelInfo
  frames_used: number
  radar_age_seconds?: number | null
  horizons: number[]
  predictions: PredictedRainCell[]
  message?: string | null
}

export type NowcastPredictRequest = {
  geometry: LatLng[]
  buffer_km?: number | null
}
