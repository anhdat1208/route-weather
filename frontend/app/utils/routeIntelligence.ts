import type { RouteIntelligenceSegment } from "~/types/routeIntelligence"

export function riskBandColor(level: string): string {
  switch (level) {
    case "low":
      return "#22c55e"
    case "moderate":
      return "#eab308"
    case "high":
      return "#f97316"
    case "severe":
      return "#ef4444"
    default:
      return "#64748b"
  }
}

export function riskBandLabel(level: string): string {
  switch (level) {
    case "low":
      return "Thấp"
    case "moderate":
      return "Trung bình"
    case "high":
      return "Cao"
    case "severe":
      return "Rất cao"
    default:
      return level
  }
}

export function rainStatusLabel(status: string | null): string {
  switch (status) {
    case "clear":
      return "Trời quang"
    case "possible_rain":
      return "Có thể mưa"
    case "light_rain":
      return "Mưa nhẹ"
    case "moderate_rain":
      return "Mưa vừa"
    case "heavy_rain":
      return "Mưa lớn"
    default:
      return status ?? "—"
  }
}

export function congestionLabel(level: string | null): string {
  switch (level) {
    case "free":
      return "Thông thoáng"
    case "slow":
      return "Chậm"
    case "moderate":
      return "Vừa phải"
    case "heavy":
      return "Nặng"
    case "severe":
      return "Rất nặng"
    default:
      return level ?? "—"
  }
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Bangkok",
  })
}

export function intelligenceSegmentGeoJson(
  segments: RouteIntelligenceSegment[],
  selectedId: string | null,
) {
  return {
    type: "FeatureCollection" as const,
    features: segments.map((seg) => ({
      type: "Feature" as const,
      geometry: {
        type: "LineString" as const,
        coordinates: seg.coordinates.map((p) => [p.lng, p.lat]),
      },
      properties: {
        id: seg.id,
        risk_level: seg.risk.travel_risk_level,
        selected: seg.id === selectedId,
        color: riskBandColor(seg.risk.travel_risk_level),
      },
    })),
  }
}

export function formatIntelligencePopup(seg: RouteIntelligenceSegment): string {
  const lineStyle = 'style="color:#e2e8f0;margin:0 0 4px 0"'
  const lines = [
    `<p ${lineStyle}><strong style="color:#f8fafc">${seg.label || seg.id}</strong></p>`,
    `<p ${lineStyle}>Đến: ${formatTime(seg.arrival_time)}</p>`,
    `<p ${lineStyle}>Thời tiết: ${rainStatusLabel(seg.weather.rain_status)} (${seg.weather.rain_probability_pct ?? 0}%)</p>`,
  ]
  if (seg.traffic?.predicted_congestion) {
    lines.push(`<p ${lineStyle}>Giao thông: ${congestionLabel(seg.traffic.predicted_congestion)}</p>`)
  }
  lines.push(
    `<p ${lineStyle}>Rủi ro: ${riskBandLabel(seg.risk.travel_risk_level)} (${seg.risk.travel_risk_score.toFixed(0)}/100)</p>`,
  )
  lines.push(
    `<p style="color:#94a3b8;font-size:11px;margin:6px 0 0 0">Độ tin cậy: ${(seg.risk.confidence * 100).toFixed(0)}%</p>`,
  )
  return `<div style="color:#e2e8f0;font-size:13px;line-height:1.45">${lines.join("")}</div>`
}
