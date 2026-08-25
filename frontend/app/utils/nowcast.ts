import type { NowcastModelInfo, PredictedRainCell } from "~/types/nowcasting"
import { bearingToCompass } from "~/utils/rainCell"

export function intensityLabel(intensity: number | null): string {
  if (intensity == null) return "Không rõ"
  if (intensity < 40) return "nhẹ"
  if (intensity < 90) return "vừa"
  return "mạnh"
}

export function nowcastModelLabel(model?: NowcastModelInfo | null): string {
  if (!model) return "Baseline v0.1"
  const name = model.name.toLowerCase() === "baseline" ? "Baseline" : model.name
  return `${name} v${model.version}`
}

function nowcastFeatureProperties(c: PredictedRainCell) {
  return {
    cell_id: c.cell_id,
    forecast_minutes: c.forecast_minutes,
    kind: c.kind,
    rain_probability: c.rain_probability,
    rain_intensity: c.rain_intensity,
    intensity_label: intensityLabel(c.rain_intensity),
    confidence: c.confidence,
    speed_kmh: c.motion?.speed_kmh ?? null,
    bearing: c.motion?.bearing_degrees ?? null,
    bearing_compass:
      c.motion?.bearing_degrees != null ? bearingToCompass(c.motion.bearing_degrees) : null,
    source: c.source,
  }
}

function percentLabel(value: unknown): string | null {
  if (value == null || value === "") return null
  const n = Number(value)
  if (Number.isNaN(n)) return null
  return `${Math.round(n * 100)}%`
}

export function formatNowcastPopup(
  featureProps: Record<string, unknown>,
  model?: NowcastModelInfo | null,
): string {
  const lineStyle = 'style="color:#e2e8f0;margin:0 0 4px 0"'
  const lines: string[] = [`<p ${lineStyle}><strong style="color:#5eead4">Nowcasting</strong></p>`]

  if (featureProps.forecast_minutes != null && featureProps.forecast_minutes !== "") {
    lines.push(`<p ${lineStyle}>Dự báo: +${Number(featureProps.forecast_minutes)} phút</p>`)
  }

  const probability = percentLabel(featureProps.rain_probability)
  lines.push(
    `<p ${lineStyle}>Xác suất mưa: ${probability ?? "Không rõ"}</p>`,
  )

  const intensity =
    (typeof featureProps.intensity_label === "string" && featureProps.intensity_label) ||
    intensityLabel(featureProps.rain_intensity != null ? Number(featureProps.rain_intensity) : null)
  lines.push(`<p ${lineStyle}>Cường độ: ${intensity}</p>`)

  const confidence = percentLabel(featureProps.confidence)
  lines.push(`<p ${lineStyle}>Độ tin cậy: ${confidence ?? "Không rõ"}</p>`)

  if (featureProps.speed_kmh != null || featureProps.bearing != null) {
    const parts: string[] = []
    if (featureProps.bearing != null) {
      const compass =
        typeof featureProps.bearing_compass === "string" && featureProps.bearing_compass
          ? featureProps.bearing_compass
          : bearingToCompass(Number(featureProps.bearing))
      parts.push(compass)
    }
    if (featureProps.speed_kmh != null) {
      parts.push(`${Number(featureProps.speed_kmh).toFixed(0)} km/h`)
    }
    lines.push(`<p ${lineStyle}>Di chuyển: ${parts.join(" · ")}</p>`)
  } else {
    lines.push(`<p ${lineStyle}>Di chuyển: không rõ</p>`)
  }

  lines.push(`<p ${lineStyle}>Mô hình: ${nowcastModelLabel(model)}</p>`)
  lines.push(
    '<p style="color:#94a3b8;font-size:11px;margin:6px 0 0 0">Dữ liệu dự báo — không phải radar quan sát</p>',
  )
  return `<div style="color:#e2e8f0;font-size:13px;line-height:1.45">${lines.join("")}</div>`
}

export function nowcastGeoJson(cells: PredictedRainCell[]) {
  const bboxFeatures = cells
    .filter((c) => c.bounds)
    .map((c) => {
      const b = c.bounds!
      return {
        type: "Feature" as const,
        geometry: {
          type: "Polygon" as const,
          coordinates: [
            [
              [b.west, b.north],
              [b.east, b.north],
              [b.east, b.south],
              [b.west, b.south],
              [b.west, b.north],
            ],
          ],
        },
        properties: nowcastFeatureProperties(c),
      }
    })

  const pointFeatures = cells.map((c) => ({
    type: "Feature" as const,
    geometry: {
      type: "Point" as const,
      coordinates: [c.centroid.lng, c.centroid.lat],
    },
    properties: nowcastFeatureProperties(c),
  }))

  return {
    bbox: { type: "FeatureCollection" as const, features: bboxFeatures },
    points: { type: "FeatureCollection" as const, features: pointFeatures },
  }
}
