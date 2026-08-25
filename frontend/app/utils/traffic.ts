import type {
  CongestionLevel,
  RoadSegment,
  TrafficModelInfo,
  TrafficPrediction,
  WeatherImpactLevel,
} from "~/types/traffic"
import { intensityLabel } from "~/utils/nowcast"

const CONGESTION_COLORS: Record<CongestionLevel, string> = {
  free: "#22c55e",
  slow: "#eab308",
  moderate: "#f97316",
  heavy: "#ef4444",
  severe: "#991b1b",
}

export function congestionColor(level: CongestionLevel | null | undefined): string {
  if (level == null) return "#64748b"
  return CONGESTION_COLORS[level]
}

export function trafficModelLabel(model?: TrafficModelInfo | null): string {
  if (!model) return "Baseline v0.1"
  const name = model.name.toLowerCase() === "baseline" ? "Baseline" : model.name
  return `${name} v${model.version}`
}

function congestionLabel(level: CongestionLevel | null | undefined): string {
  if (level == null) return "Không rõ"
  const labels: Record<CongestionLevel, string> = {
    free: "Thông thoáng",
    slow: "Chậm",
    moderate: "Tắc vừa",
    heavy: "Tắc nặng",
    severe: "Tắc nghiêm trọng",
  }
  return labels[level]
}

function weatherImpactLabel(level: WeatherImpactLevel | null | undefined): string {
  if (level == null) return "Không rõ"
  const labels: Record<WeatherImpactLevel, string> = {
    none: "Không",
    low: "Thấp",
    moderate: "Trung bình",
    high: "Cao",
  }
  return labels[level]
}

function speedLabel(value: unknown): string {
  if (value == null || value === "") return "Không rõ"
  const n = Number(value)
  if (Number.isNaN(n)) return "Không rõ"
  return `${Math.round(n)} km/h`
}

function percentLabel(value: unknown): string | null {
  if (value == null || value === "") return null
  const n = Number(value)
  if (Number.isNaN(n)) return null
  const pct = Math.round(n * 100)
  return `${pct >= 0 ? "+" : ""}${pct}%`
}

function segmentFeatureProperties(
  segment: RoadSegment,
  mode: "current" | "predicted",
  prediction?: TrafficPrediction,
) {
  const traffic = segment.traffic
  const congestion =
    mode === "predicted" ? prediction?.predicted_congestion : traffic?.congestion_level
  const speed =
    mode === "predicted" ? prediction?.predicted_speed_kmh : traffic?.current_speed_kmh

  return {
    segment_id: segment.id,
    name: segment.name ?? null,
    road_type: segment.road_type ?? null,
    mode,
    color: congestionColor(congestion),
    congestion_level: congestion ?? null,
    congestion_label: congestionLabel(congestion),
    speed_kmh: speed ?? null,
    current_speed_kmh: traffic?.current_speed_kmh ?? null,
    free_flow_speed_kmh: traffic?.free_flow_speed_kmh ?? null,
    current_congestion: traffic?.congestion_level ?? null,
    current_congestion_label: congestionLabel(traffic?.congestion_level),
    relative_speed: traffic?.relative_speed ?? null,
    source: traffic?.source ?? null,
    stale: traffic?.stale ?? false,
    forecast_minutes: prediction?.forecast_minutes ?? null,
    predicted_speed_kmh: prediction?.predicted_speed_kmh ?? null,
    predicted_congestion: prediction?.predicted_congestion ?? null,
    predicted_congestion_label: congestionLabel(prediction?.predicted_congestion),
    confidence: prediction?.confidence ?? null,
    base_speed_delta_pct: prediction?.base_prediction.speed_delta_pct ?? null,
    weather_impact_level: prediction?.weather_impact.level ?? null,
    weather_impact_delta_pct: prediction?.weather_impact.speed_delta_pct ?? null,
    weather_adjusted_delta_pct: prediction?.weather_adjusted.speed_delta_pct ?? null,
    rain_probability: prediction?.weather_impact.rain_probability ?? null,
    rain_intensity: prediction?.weather_impact.rain_intensity ?? null,
    rain_intensity_label:
      prediction?.weather_impact.rain_intensity != null
        ? intensityLabel(prediction.weather_impact.rain_intensity)
        : null,
  }
}

export function trafficLineGeoJson(
  segments: RoadSegment[],
  predictionsForHorizon: TrafficPrediction[],
  mode: "current" | "predicted",
) {
  const predictionBySegment = new Map(
    predictionsForHorizon.map((p) => [p.road_segment_id, p]),
  )

  const features = segments.flatMap((segment) => {
    if (segment.geometry.length < 2) return []

    const prediction = mode === "predicted" ? predictionBySegment.get(segment.id) : undefined
    if (mode === "predicted" && !prediction) return []

    return [
      {
        type: "Feature" as const,
        geometry: {
          type: "LineString" as const,
          coordinates: segment.geometry.map((p) => [p.lng, p.lat]),
        },
        properties: segmentFeatureProperties(segment, mode, prediction),
      },
    ]
  })

  return { type: "FeatureCollection" as const, features }
}

export function formatTrafficPopup(
  featureProps: Record<string, unknown>,
  model?: TrafficModelInfo | null,
): string {
  const lineStyle = 'style="color:#e2e8f0;margin:0 0 4px 0"'
  const isPredicted = featureProps.mode === "predicted"
  const title = isPredicted ? "Dự báo giao thông" : "Giao thông"
  const titleColor = isPredicted ? "#fdba74" : "#86efac"
  const lines: string[] = [`<p ${lineStyle}><strong style="color:${titleColor}">${title}</strong></p>`]

  const roadName =
    typeof featureProps.name === "string" && featureProps.name.trim()
      ? featureProps.name
      : null
  lines.push(
    `<p ${lineStyle}>Đoạn: ${roadName ?? String(featureProps.segment_id ?? "Không rõ")}</p>`,
  )

  lines.push(
    `<p ${lineStyle}>Tốc độ hiện tại: ${speedLabel(featureProps.current_speed_kmh)}</p>`,
    `<p ${lineStyle}>Tắc hiện tại: ${
      (typeof featureProps.current_congestion_label === "string" &&
        featureProps.current_congestion_label) ||
      congestionLabel(featureProps.current_congestion as CongestionLevel | null)
    }</p>`,
  )

  if (isPredicted) {
    if (featureProps.forecast_minutes != null && featureProps.forecast_minutes !== "") {
      lines.push(`<p ${lineStyle}>Dự báo: +${Number(featureProps.forecast_minutes)} phút</p>`)
    }
    lines.push(
      `<p ${lineStyle}>Tốc độ dự báo: ${speedLabel(featureProps.predicted_speed_kmh)}</p>`,
      `<p ${lineStyle}>Tắc dự báo: ${
        (typeof featureProps.predicted_congestion_label === "string" &&
          featureProps.predicted_congestion_label) ||
        congestionLabel(featureProps.predicted_congestion as CongestionLevel | null)
      }</p>`,
    )

    const impactLevel =
      (typeof featureProps.weather_impact_level === "string" && featureProps.weather_impact_level) ||
      null
    lines.push(
      `<p ${lineStyle}>Ảnh hưởng thời tiết: ${weatherImpactLabel(impactLevel as WeatherImpactLevel | null)}</p>`,
    )

    const rainProb = percentLabel(featureProps.rain_probability)
    if (rainProb != null || featureProps.rain_intensity != null) {
      const intensity =
        (typeof featureProps.rain_intensity_label === "string" && featureProps.rain_intensity_label) ||
        (featureProps.rain_intensity != null
          ? intensityLabel(Number(featureProps.rain_intensity))
          : "Không rõ")
      lines.push(
        `<p ${lineStyle}>Mưa dự báo: ${rainProb ?? "Không rõ"} · Cường độ: ${intensity}</p>`,
      )
    }

    const confidence = percentLabel(featureProps.confidence)
    lines.push(`<p ${lineStyle}>Độ tin cậy: ${confidence ?? "Không rõ"}</p>`)

    const baseTrend = percentLabel(featureProps.base_speed_delta_pct)
    const weatherDelta = percentLabel(featureProps.weather_impact_delta_pct)
    const combined = percentLabel(featureProps.weather_adjusted_delta_pct)
    if (baseTrend != null || weatherDelta != null || combined != null) {
      lines.push(
        `<p ${lineStyle}>Xu hướng nền: ${baseTrend ?? "Không rõ"} · Thời tiết: ${weatherDelta ?? "Không rõ"} · Tổng hợp: ${combined ?? "Không rõ"}</p>`,
      )
    }
  }

  lines.push(`<p ${lineStyle}>Mô hình: ${trafficModelLabel(model)}</p>`)
  lines.push(
    '<p style="color:#94a3b8;font-size:11px;margin:6px 0 0 0">Dự báo baseline v0.1 — giao thông synthetic (không phải live)</p>',
  )

  return `<div style="color:#e2e8f0;font-size:13px;line-height:1.45">${lines.join("")}</div>`
}
