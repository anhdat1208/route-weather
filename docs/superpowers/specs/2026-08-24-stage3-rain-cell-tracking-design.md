# Route Weather Stage 3 — Rain-cell Detection & Tracking — Design Specification

> Approved: 2026-08-24  
> Approach: **Backend corridor track** (Approach 1)  
> Builds on Stage 1 (Route Weather MVP) and Stage 2 (Live Radar / RainViewer)

## 1. Product Goal

Stage 2 answers: *"Where is precipitation right now?"*

Stage 3 begins answering: *"What precipitation cells exist, and how are they moving?"*

```text
Radar Frames
  → Rain-cell Detection
  → Cell Identification
  → Cell Tracking
  → Movement Vector (speed + bearing)
  → Map Visualization
```

This is a **deterministic baseline**. Output feeds future nowcasting; Stage 3 itself does **not** predict future precipitation or route risk.

## 2. Decisions Locked

| Topic | Decision |
|---|---|
| Strategy | Backend processing pipeline; do not detect inside map/UI |
| Geographic scope | Route corridor: route geometry bounding box + configurable buffer |
| Activation | UI toggle “Rain cells” ON **and** a computed route exists |
| Radar provider | Reuse Stage 2 RainViewer (extend adapter; do not rewrite overlay) |
| Frame history | Use RainViewer `radar.past` (small configurable count); polite tile fetch |
| Intensity source | Decode RainViewer PNG tiles in corridor → normalized intensity grid |
| Detection | Threshold + connected-component labeling (4-connected) + area filters |
| Tracking | Centroid distance (haversine) + area/intensity similarity + bbox overlap |
| Motion | Geographic haversine displacement + Δt → speed km/h + bearing degrees |
| Risk / forecast | Out of scope (no risk %, no future positions as forecasts) |
| AI / ML | None |
| Config on Vercel | Optional overrides only; sensible defaults in `Settings` |
| Git branch | Implement on `feat/stage3-rain-cell-tracking` branched from `main` |

## 3. Existing Stage 2 Context (constraints)

| Item | Current state |
|---|---|
| Provider | RainViewer Weather Maps API |
| Stage 2 API | `GET /api/radar/current` → tile URL template + timestamp + legend |
| Client overlay | MapLibre raster tiles (Universal Blue, max zoom 7) |
| History available | `radar.past` ~2 hours, ~10-minute steps (provider JSON) |
| Intensity grid | **Not yet fetched** — Stage 3 must add tile download + decode |
| Frontend | Nuxt 4 / Vue 3 / `useRadar` / `RouteMap` |
| Backend | FastAPI; business logic owned by backend |

## 4. System Architecture

```text
RainViewer (weather-maps.json + PNG tiles)
        ↓
Radar Adapter (extend Stage 2 provider)
        ↓
Normalized RadarFrame (intensity grid + bounds + timestamp)
        ↓
Rain-cell Detection Engine
        ↓
Detected Cells
        ↓
Tracking Engine
        ↓
Tracked Cells + CellMotion
        ↓
POST /api/rain-cells/track
        ↓
useRainCells → RouteMap (Rain Cell layer)
```

### Responsibility boundaries

| Layer | Does | Does not |
|---|---|---|
| `RainViewerProvider` | Frame list; fetch tiles for bbox | Detect / track |
| Frame normalizer | Mosaic tiles → internal grid | UI rendering |
| Detection engine | Threshold, CCL, noise filter | Identity / motion |
| Tracking engine | Match, states, history, motion | Future prediction |
| Rain-cell service / API | Orchestrate + apply config | Vue business logic |
| `RouteMap` | Draw normalized tracked cells | Algorithms |

Stage 2 radar overlay remains independent and functional when rain cells are off.

## 5. Normalized Models

Adapt field names to existing Pydantic / TypeScript conventions (`lat`/`lng` where the project already uses them).

### RadarFrame

```typescript
interface RadarFrame {
  timestamp: string
  width: number
  height: number
  bounds: { north: number; south: number; east: number; west: number }
  data: number[][] // intensity grid (provider-derived units)
  source: "rainviewer"
}
```

### RainCell (per-frame detection)

```typescript
interface RainCell {
  id: string
  timestamp: string
  centroid: { lat: number; lng: number }
  areaKm2?: number
  intensity?: { min?: number; max?: number; mean?: number }
  bounds?: { north: number; south: number; east: number; west: number }
  geometry?: unknown // optional bbox polygon for map
}
```

### CellMotion

```typescript
interface CellMotion {
  speedKmh?: number
  bearingDegrees?: number
  from?: { lat: number; lng: number }
  to?: { lat: number; lng: number }
  confidence?: number // engineering match quality 0–1, not AI
}
```

### TrackedCell

```typescript
type TrackState = "NEW" | "TRACKING" | "LOST" | "EXPIRED"

interface TrackedCell {
  id: string
  state: TrackState
  current: RainCell
  history: RainCell[]
  motion?: CellMotion
  distanceToRouteKm?: number // optional proximity only
  missedFrames: number
}
```

## 6. API Surface

| Method | Path | Role |
|---|---|---|
| `GET` | `/api/radar/current` | Unchanged (Stage 2) |
| `POST` | `/api/rain-cells/track` | Detect + track for route corridor |

### `POST /api/rain-cells/track`

**Request (conceptual):**

```json
{
  "geometry": [{ "lat": 10.8, "lng": 106.7 }, "..."],
  "buffer_km": null
}
```

- `geometry`: route polyline (required).
- `buffer_km`: optional override; default from settings.

**Response (conceptual):**

```json
{
  "status": "ok" | "partial" | "unavailable",
  "frames_used": 4,
  "cells": [ /* TrackedCell */ ],
  "message": null
}
```

No separate public `detect` endpoint required for UI. Detection remains a pure engine function for unit tests.

UI calls track only when the rain-cell toggle is on **and** route weather geometry is available.

## 7. Configuration

All thresholds are **implementation parameters**, not authoritative meteorological classifications. Document that distinction in README.

| Variable | Purpose | Suggested default |
|---|---|---|
| `RAIN_CELL_MIN_INTENSITY` | Pixel intensity threshold | Tuned from RainViewer decode scale |
| `RAIN_CELL_MIN_AREA` | Drop noise / tiny regions | Small connected area (pixels or km²) |
| `RAIN_CELL_MAX_AREA` | Optional upper bound | Large / unlimited with sane cap |
| `RAIN_CELL_MAX_MATCH_DISTANCE_KM` | Max centroid match distance | e.g. tens of km per frame step |
| `RAIN_CELL_HISTORY_FRAMES` | Per-cell history retention | e.g. 6 |
| `RAIN_CELL_MAX_MISSED_FRAMES` | LOST → EXPIRED tolerance | e.g. 2 |
| `RAIN_CELL_FRAME_COUNT` | Past frames to process | e.g. 4–6 |
| `RAIN_CELL_BUFFER_KM` | Corridor padding around route | e.g. 50 |
| `RAIN_CELL_TILE_ZOOM` | Decode zoom (≤ RainViewer max 7) | e.g. 5–6 |

**Vercel:** variables are optional. Defaults in `Settings` must make production work without dashboard configuration. Set env only to tune without code changes.

Respect RainViewer rate/terms: cache metadata, limit tile count per request, do not aggressively backfill history.

## 8. Algorithms

### 8.1 Intensity grid construction

1. Compute route bbox + `RAIN_CELL_BUFFER_KM`.
2. Fetch latest `RAIN_CELL_FRAME_COUNT` entries from RainViewer `radar.past` (oldest → newest).
3. For each frame, download PNG tiles covering the bbox at `RAIN_CELL_TILE_ZOOM`.
4. Decode pixels to intensity:
   - Prefer a raw / black-and-white dBZ scheme if usable with the public API.
   - Otherwise map Universal Blue palette colors using RainViewer’s published color table.
5. Mosaic into a single `RadarFrame` grid with geographic bounds.
6. Transparent / missing pixels → invalid / zero (documented); do not invent coverage.

### 8.2 Detection

1. Binary mask: `intensity >= RAIN_CELL_MIN_INTENSITY` (valid pixels only).
2. 4-connected connected-component labeling.
3. Filter components by min/max area.
4. Emit `RainCell` with centroid (pixel → lat/lng), bounds, intensity stats, area.

This is **not** meteorological storm-cell typing. It is contiguous precipitation-region detection above an engineering threshold.

### 8.3 Tracking

For consecutive frames T0 → T1 → …:

1. Score candidate pairs: centroid haversine distance, area similarity, intensity similarity, bbox overlap.
2. Greedy / bipartite-style best matches under `RAIN_CELL_MAX_MATCH_DISTANCE_KM`.
3. Matched → keep `id`, state `TRACKING` (first appearance `NEW`).
4. Unmatched previous → `LOST`, increment `missedFrames`; if `> MAX_MISSED` → `EXPIRED`.
5. Unmatched current → new `id`, state `NEW`.
6. Append `current` to `history`, truncate to `RAIN_CELL_HISTORY_FRAMES`.
7. Optional: `distanceToRouteKm` = min haversine distance from centroid to route polyline.

### 8.4 Motion

Given matched positions at T0 and T1:

- Displacement = haversine meters (reuse / extend `geo_math`).
- `speedKmh` = (meters / Δt_seconds) * 3.6.
- `bearingDegrees` = initial bearing on WGS84 (0–360).
- Do **not** treat lat/lng deltas as Cartesian meters.
- Do **not** present extrapolated future positions as forecasts in UI.

`confidence` = simple blend of match score factors (distance, overlap, area/intensity similarity, consecutive hits). Engineering indicator only.

## 9. Frontend

### Map layers (order)

```text
Base → Radar (Stage 2) → Rain Cells (Stage 3) → Route → Weather points
```

### Visualization (lightweight)

- Centroid marker
- Optional bounding box / simple polygon
- Direction arrow when `motion` is available
- Click/popup: intensity summary (if derived), area, movement direction, speed, updated time, optional distance to route
- Omit unavailable fields; do not fabricate values

### Composable

`useRainCells`: toggle, loading/error, fetch track when enabled + route present, refresh alignment with radar cadence where practical, expose `TrackedCell[]` to `RouteMap`.

Controls: extend radar panel or adjacent toggle — keep UI simple; Vietnamese copy consistent with existing app.

## 10. Performance & quality

- All heavy decode/detect/track runs on **backend** so the UI thread stays responsive.
- Bound tile count via zoom + corridor buffer; cache weather-maps JSON like Stage 2.
- Basic noise filtering: min intensity, min area, invalid pixel handling.
- Document clutter / artifacts as known limitations of a baseline detector.

## 11. Testing

Synthetic intensity grids (unit tests only — never shown as live weather in production UI):

| Test | Expectation |
|---|---|
| Single cell | One region detected |
| Multiple cells | Separated regions → multiple cells |
| Noise | Isolated weak pixels filtered |
| Tracking | Displaced cell keeps identity |
| Movement | Approximate speed + bearing |
| Disappearance | LOST before EXPIRED |
| New cell | New identity |
| Stage 1/2 regression | Route, weather, radar, responsive map |

Run: backend `pytest`, frontend typecheck/build, lint as project already does.

## 12. Documentation

Update root `README.md` with Stage 3 section:

- Implemented: detection, filtering, identity, tracking, speed/direction, history, map layer
- Not implemented: AI/ML, future precip prediction, route risk scoring, traffic, satellite
- Algorithms, thresholds, limitations, RainViewer assumptions
- Explicit: deterministic baseline

## 13. Out of Scope (explicit)

- Gemini / LLM / ML / neural tracking
- Authoritative future positions / nowcast probabilities
- Final route risk engine (“HIGH RISK”, % scores for travel advice)
- Satellite fusion, traffic prediction
- Rewriting Stage 2 radar display pipeline

## 14. Definition of Done

- [ ] Normalized `RadarFrame` from RainViewer corridor tiles
- [ ] Configurable detection thresholds
- [ ] Multi-cell detection + noise filtering
- [ ] Persistent IDs + NEW/TRACKING/LOST/EXPIRED
- [ ] Configurable history retention
- [ ] Speed + bearing via geographic math
- [ ] Map visualization + cell info (no fabricated fields)
- [ ] Stage 1/2 route, weather, radar still work; UI remains responsive
- [ ] Synthetic unit tests for detect/track/motion/lifecycle
- [ ] No AI/ML; no future prediction UX; no final risk engine
- [ ] README updated; tests / typecheck / build pass
- [ ] Work landed on branch from `main` (`feat/stage3-rain-cell-tracking`)

## 15. Future handoff (not Stage 3)

```text
Motion / short history
  → Route proximity (already optional here)
  → Trajectory / nowcasting (Stage 5+)
  → Route risk (later)
```

Stage 3 stops at **observed motion + track history**.
