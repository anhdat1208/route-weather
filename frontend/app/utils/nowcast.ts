import type { PredictedRainCell } from "~/types/nowcasting"
import { bearingToCompass } from "~/utils/rainCell"

export function intensityLabel(intensity: number | null): string {
  if (intensity == null) return "Không rõ"
  if (intensity < 40) return "nhẹ"
  if (intensity < 90) return "vừa"
  return "mạnh"
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
        properties: {
          cell_id: c.cell_id,
          forecast_minutes: c.forecast_minutes,
          kind: c.kind,
        },
      }
    })

  const pointFeatures = cells.map((c) => ({
    type: "Feature" as const,
    geometry: {
      type: "Point" as const,
      coordinates: [c.centroid.lng, c.centroid.lat],
    },
    properties: {
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
    },
  }))

  return {
    bbox: { type: "FeatureCollection" as const, features: bboxFeatures },
    points: { type: "FeatureCollection" as const, features: pointFeatures },
  }
}
