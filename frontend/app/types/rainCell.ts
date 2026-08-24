import type { LatLng } from "~/types/routeWeather"

export type TrackState = "NEW" | "TRACKING" | "LOST" | "EXPIRED"
export type RainCellTrackStatus = "ok" | "partial" | "unavailable"

export type CellIntensity = {
  min?: number | null
  max?: number | null
  mean?: number | null
}

export type CellBounds = {
  north: number
  south: number
  east: number
  west: number
}

export type RainCell = {
  id: string
  timestamp: string
  centroid: LatLng
  area_km2?: number | null
  intensity?: CellIntensity | null
  bounds?: CellBounds | null
}

export type CellMotion = {
  speed_kmh?: number | null
  bearing_degrees?: number | null
  from_point?: LatLng | null
  to_point?: LatLng | null
  confidence?: number | null
}

export type TrackedRainCell = {
  id: string
  state: TrackState
  current: RainCell
  history: RainCell[]
  motion?: CellMotion | null
  distance_to_route_km?: number | null
  missed_frames: number
}

export type RainCellTrackResponse = {
  status: RainCellTrackStatus
  frames_used: number
  cells: TrackedRainCell[]
  message?: string | null
}

export type RainCellTrackRequest = {
  geometry: LatLng[]
  buffer_km?: number | null
}
