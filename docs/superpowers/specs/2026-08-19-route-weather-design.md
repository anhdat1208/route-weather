# Route Weather MVP — Design Specification

> Approved: 2026-08-19
> Stack: Phương án 1 — Monorepo Nuxt 4 + FastAPI + PostgreSQL + GraphHopper + Open-Meteo

## 1. Product Goal

Answer: *"If I travel from A to B at a specific time, what weather conditions am I likely to encounter along the route?"*

Maps weather forecasts onto a journey in both **space** and **time**. Not a generic weather app. No radar, satellite, AI analysis, or Local Rain features.

## 2. External Services & Billing

| Service | Role | Key Required | Free Tier | Billing at Signup |
|---|---|---|---|---|
| GraphHopper Cloud | Routing + Geocoding | Yes | 500 credits/day, 0€ | **No credit card required** |
| Open-Meteo | Weather forecast | No | Unlimited (fair use) | N/A |
| OpenFreeMap | Map tiles (MapLibre) | No | Free | N/A |
| PostgreSQL | Cache only | No | Self-hosted (Docker) | N/A |

**Important GraphHopper limitation:** Free plan is **non-commercial use only**. For production/commercial deployment, upgrade to a paid plan (Basic 69€/month).

**Credit budget estimate (MVP dev):**
- 1 route request ≈ 1 credit
- 1 geocode request ≈ 0.3–0.9 credits
- 500 credits/day is sufficient for development and light personal use

## 3. System Architecture

```
Frontend (Nuxt 4)  →  FastAPI Backend  →  Route Weather Engine
                                              ├── RouteService → GraphHopperRouteProvider
                                              ├── GeocodeService → GraphHopperGeocodeProvider
                                              ├── WeatherService → OpenMeteoProvider
                                              └── Cache → PostgreSQL
```

Backend owns all business logic. Frontend renders pre-computed results only. Never show fake weather data.

## 4. Provider Abstractions

```python
class GeocodeProvider(Protocol):
    async def search(query: str, limit: int) -> list[GeocodeResult]
    async def reverse(lat: float, lng: float) -> GeocodeResult

class RouteProvider(Protocol):
    async def get_route(origin, destination, travel_mode, departure_time) -> RouteResult

class WeatherProvider(Protocol):
    async def get_forecast(lat, lng, time) -> WeatherForecast
    async def get_forecast_batch(points) -> list[WeatherForecast]
```

Travel mode mapping: `motorbike` → GraphHopper `motorcycle`, `walking` → `foot`.

## 5. Route Weather Engine

1. Geocode text inputs (if needed)
2. Get route (geometry, distance, duration)
3. Simplify geometry (Douglas-Peucker)
4. Sample 5–20 representative points (distance-based)
5. Calculate ETA per point (proportional to cumulative distance)
6. Batch-query weather at each point + arrival time
7. Calculate risk per segment + overall route risk
8. Generate departure time recommendation

**Sampling rules:**

| Distance | Points |
|---|---|
| < 5 km | 5 |
| 5–15 km | 8–12 |
| 15–50 km | 12–15 |
| > 50 km | 15–20 |

Config: `ROUTE_WEATHER_MAX_POINTS=20`, `ROUTE_WEATHER_MIN_POINTS=5`.

## 6. Weather Risk Formula

**Segment risk (0–100):**
```
segment_risk = (
    precipitation_probability × 0.50 +
    precipitation_intensity   × 0.25 +
    wind_speed_factor         × 0.10 +
    visibility_factor         × 0.15
) × 100
```

**Overall route risk:**
```
overall_risk = max_segment × 0.40 + avg_segment × 0.30 + exposure_ratio × 0.30
```

**Precipitation labels:** 0–20% LOW, 20–40% MODERATE-LOW, 40–60% MODERATE, 60–80% HIGH, 80–100% VERY HIGH.

All thresholds configurable via environment variables.

## 7. API Endpoints

- `POST /api/route-weather` — Main calculation
- `POST /api/route-weather/compare` — Compare departure times
- `GET /api/geocode?q=...&limit=5` — Address autocomplete
- `GET /api/health` — Health check

## 8. UI Design (Based on Approved Mockup)

### 8.1 Visual Identity

- **Theme:** Dark mode default (navy/charcoal), optional light mode toggle
- **Backgrounds:** `#0F172A` (page), `#1E293B` (cards)
- **Accent gradient:** `#3B82F6` → `#8B5CF6` (CTA button)
- **Risk colors:** Green `#22C55E`, Lime `#84CC16`, Yellow `#F59E0B`, Orange `#F97316`, Red `#EF4444`
- **Typography:** Inter or similar clean sans-serif
- **Style:** Rounded cards, subtle shadows, glassmorphism on floating elements
- **Language:** Vietnamese UI text throughout

### 8.2 Desktop Layout

Two-column: Sidebar (~320px) + Main content (flex).

**Left Sidebar:**
1. Header — Logo "Route Weather" + tagline "Biết thời tiết trên từng chặng đường"
2. Input card — Origin (green pin), Destination (red pin), Transport mode dropdown, Departure time picker, CTA button "Tìm lộ trình & thời tiết"
3. Journey summary card — Distance, travel time, departure, ETA
4. Weather risk gauge — Circular progress showing score/100 + level label + subtext (e.g. "Bạn có khả năng gặp mưa trên 7.2 km")
5. Recommendation card — "Gợi ý" with departure time suggestion

**Main Content (top):**
- Tab bar: "Bản đồ" | "Timeline" | "So sánh thời gian" + Share button + Dark/Light toggle
- Full MapLibre map with dark style
- Route polyline color-coded by weather risk
- Origin marker (green), destination marker (red)
- Floating weather widget (current local weather)
- Map legend card ("Chú thích") explaining color codes
- Zoom controls + "My Location" button

**Main Content (bottom):**
- Timeline header: "Thời tiết trên lộ trình" + toggle "Chặng đường" / "Thời gian"
- Horizontal weather stepper — each point shows: time, location name, weather icon, rain %, label, temperature
- Highest-risk point highlighted with red semi-transparent box
- Distance scale bar below (color-coded, matching route)
- Info banner at bottom with segment detail (e.g. "Đoạn từ Tân Bình đến Bàu Cát có khả năng mưa cao nhất...")

### 8.3 Mobile Layout

- Map full-screen
- Bottom sheet for: input form, summary, timeline, risk score
- Swipeable bottom sheet states (collapsed / half / full)
- Tab navigation preserved but adapted for mobile

### 8.4 Key UI Components

| Component | Description |
|---|---|
| `RouteForm.vue` | Origin/dest autocomplete, mode, time, CTA |
| `RouteMap.vue` | MapLibre with colored segments, markers, legend |
| `RiskGauge.vue` | Circular progress gauge (score/100) |
| `WeatherTimeline.vue` | Horizontal stepper with weather data |
| `DepartureComparison.vue` | Side-by-side departure time risk comparison |
| `SegmentDetail.vue` | Popup/modal for segment weather details |
| `JourneySummary.vue` | Distance, duration, times card |
| `RecommendationCard.vue` | Departure time suggestion |

## 9. Caching

Single PostgreSQL table `cache_entries(key, value JSONB, expires_at)`.

| Type | TTL | Key pattern |
|---|---|---|
| Route | 24h | `route:{origin}:{dest}:{mode}` |
| Geocode | 7d | `geocode:{query}` |
| Weather | 30min | `weather:{lat}:{lng}:{hour}` |

## 10. Error Handling

- Routing failure → "Không tìm được lộ trình"
- Weather failure → "Lộ trình đã tìm được, nhưng thông tin thời tiết tạm thời không khả dụng"
- Geocoding failure → "Không tìm thấy địa chỉ"
- Forecast unavailable for time → "Dự báo không khả dụng cho thời gian đã chọn"
- Never show fake/fallback weather data

## 11. Testing

Core engine unit tests: sampler, ETA, risk calculation, precipitation classification, departure time comparison, missing data handling, provider failures.

Critical test: same route + different departure time → different weather/risk results.

## 12. Known Limitations (MVP)

- Open-Meteo hourly resolution (ETA at :48 uses :00 forecast)
- GraphHopper free tier 500 credits/day, non-commercial only
- No traffic-aware ETA
- Geocoding accuracy varies for small Vietnamese streets
- Forecasts are probabilistic — UI must always communicate this
