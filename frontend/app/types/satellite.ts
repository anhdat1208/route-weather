export type SatelliteStatus = "ok" | "stale" | "unavailable"

export interface SatelliteFrameResponse {
  status: SatelliteStatus
  provider: string
  source: string
  timestamp: string | null
  observed_at: string | null
  received_at: string | null
  tile_url_template: string | null
  tile_matrix_set: string | null
  tile_format: string | null
  tile_max_zoom: number
  refresh_interval_seconds: number
  stale_after_seconds: number
  coverage: string
  message: string | null
}
