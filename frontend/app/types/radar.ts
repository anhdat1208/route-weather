export type RadarStatus = "ok" | "stale" | "unavailable"

export interface RadarLegendStop {
  label: string
  color: string
}

export interface RadarLegend {
  provider: string
  scheme: string
  title: string
  stops: RadarLegendStop[]
}

export interface RadarFrameResponse {
  status: RadarStatus
  provider: string
  timestamp: string | null
  generated_at: string | null
  tile_url_template: string | null
  tile_max_zoom: number
  refresh_interval_seconds: number
  stale_after_seconds: number
  legend: RadarLegend | null
  coverage: string
  message: string | null
}
