# Route Weather

Ứng dụng lập kế hoạch lộ trình kèm dự báo thời tiết theo không gian và thời gian.

> "Nếu tôi đi từ A đến B, tôi sẽ gặp thời tiết gì trên đường và lúc nào?"

## Stage 1 scope

**Có:** nhập origin/destination (+ phương tiện, giờ xuất phát), tính route trên map, sampling điểm theo interval cấu hình được, ETA từng điểm, weather normalized qua adapter, timeline thời tiết, loading/error, weather fail không làm mất route.

**Không có (giai đoạn sau):** satellite, rain-cell tracking, AI nowcasting, traffic prediction, risk scoring trên UI.

## Stage 2 — Live Radar

Stage 2 bổ sung radar mưa gần thời gian thực lên bản đồ lộ trình.

**Có thêm:**
- Radar mưa gần thời gian thực (RainViewer)
- Lớp radar trên map, bật/tắt và điều chỉnh độ mờ
- Legend cường độ mưa, timestamp/độ tươi dữ liệu
- Tự làm mới theo chu kỳ cấu hình được
- Route vẫn hiển thị rõ trên radar (lớp glow)

**Chưa có:** dự báo chuyển động mưa tương lai, AI nowcasting, route risk UI, traffic prediction.

## Stage 3 — Rain-cell Detection & Tracking

Stage 3 **diễn giải** dữ liệu radar để phát hiện vùng mưa và theo dõi chuyển động qua các khung radar liên tiếp.

**Có thêm:**
- Phát hiện vùng mưa (connected regions) trong hành lang lộ trình
- Lọc nhiễu theo ngưỡng cấu hình được
- Theo dõi identity vùng mưa qua các khung radar (`NEW` / `TRACKING` / `LOST`)
- Tốc độ và hướng di chuyển quan sát (haversine + bearing)
- Lịch sử ngắn theo khung radar
- Lớp vùng mưa trên map (bbox, centroid, vector hướng)
- Popup thông tin khi click vùng mưa
- Khoảng cách vùng mưa tới lộ trình (không có route risk scoring)

**Chưa có:** AI/ML, dự báo vị trí mưa tương lai, route risk scoring, traffic prediction, satellite fusion.

Thuật toán baseline **deterministic** (threshold + connected components + centroid matching). Ngưỡng intensity là **implementation threshold**, không phải phân loại khí tượng chính thức.

```text
RainViewer tiles (corridor)
  → intensity grid
  → detect cells
  → track across past frames
  → POST /api/rain-cells/track
  → useRainCells → RouteMap
```

## Tech Stack

- **Frontend:** Nuxt 4, Vue 3, TypeScript, Tailwind CSS, MapLibre GL JS
- **Backend:** Python 3.12, FastAPI
- **Routing/Geocoding:** GraphHopper Cloud
- **Weather:** Open-Meteo (normalized → internal model → UI)

## Architecture

```text
User → RouteForm
         ↓
  useRouteWeather ──→ POST /api/route-weather → RouteWeatherEngine
  useRadar       ──→ GET /api/radar/current  → RadarService → RainViewer
  useRainCells   ──→ POST /api/rain-cells/track → RainCellService
  useNowcasting  ──→ POST /api/nowcasting/predict → NowcastingService
  useTraffic     ──→ POST /api/traffic/prediction → TrafficService
         ↓
  RouteMap (Base → Radar → Rain Cells → Predicted nowcast → Traffic → Route → Weather points)
         +
  RadarControls + JourneySummary + WeatherTimeline
```

Map layers: Base → Radar (Stage 2) → Rain Cells (Stage 3) → Predicted nowcast (Stage 5) → Traffic (Stage 6) → Route → Weather points.

## Yêu cầu

- Docker & Docker Compose (tùy chọn)
- Node.js 22+ (frontend)
- Python 3.12+ (backend)

## Bắt đầu nhanh

### 1. Cấu hình môi trường

```bash
cp .env.example .env
```

Thêm `GRAPHHOPPER_API_KEY` (đăng ký miễn phí tại [graphhopper.com](https://www.graphhopper.com)).

### 2. Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

### 3. Dev local

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
cd backend
python -m pytest
```

```bash
cd frontend
npm run build
```

## Environment variables

| Variable | Mô tả |
|---|---|
| `GRAPHHOPPER_API_KEY` | API key GraphHopper |
| `GRAPHHOPPER_BASE_URL` | GraphHopper API base |
| `OPEN_METEO_BASE_URL` | Open-Meteo API base |
| `RAINVIEWER_API_URL` | RainViewer API base (radar tiles) |
| `RADAR_REFRESH_INTERVAL_SECONDS` | Chu kỳ làm mới radar phía client, mặc định `300` |
| `RADAR_STALE_AFTER_SECONDS` | Coi radar cũ sau N giây, mặc định `900` |
| `CACHE_TTL_RADAR` | Cache metadata radar (giây), mặc định `120` |
| `SATELLITE_REFRESH_INTERVAL_SECONDS` | Chu kỳ làm mới satellite phía client, mặc định `600` |
| `SATELLITE_STALE_AFTER_SECONDS` | Coi satellite cũ sau N giây, mặc định `1800` |
| `CACHE_TTL_SATELLITE` | Cache metadata satellite (giây), mặc định `300` |
| `FORECAST_STALE_AFTER_SECONDS` | Ngưỡng stale forecast trong fusion, mặc định `3600` |
| `FUSION_ALIGNMENT_MAX_SECONDS` | Ngưỡng lệch thời gian radar-satellite để đánh dấu conflict, mặc định `1200` |
| `FUSION_CORRIDOR_KM` | Bán kính hành lang gán rain-cell vào segment, mặc định `25` |
| `GIBS_WMTS_CAPABILITIES_URL` | WMTS capabilities URL cho NASA GIBS |
| `GIBS_SATELLITE_LAYER` | Layer vệ tinh GIBS (mặc định Himawari IR Band13) |
| `GIBS_TILE_MATRIX_SET` | Tile matrix set GIBS (mặc định `GoogleMapsCompatible_Level6`) |
| `GIBS_TILE_MAX_ZOOM` | Max zoom layer satellite, mặc định `6` |
| `RAIN_CELL_MIN_INTENSITY` | Ngưỡng intensity pixel (implementation), mặc định `25` |
| `RAIN_CELL_MIN_AREA_PIXELS` | Diện tích tối thiểu (pixel), mặc định `4` |
| `RAIN_CELL_MAX_AREA_PIXELS` | Diện tích tối đa (pixel), mặc định `500000` |
| `RAIN_CELL_MAX_MATCH_DISTANCE_KM` | Khoảng cách match centroid, mặc định `80` |
| `RAIN_CELL_HISTORY_FRAMES` | Số khung lịch sử giữ lại, mặc định `6` |
| `RAIN_CELL_MAX_MISSED_FRAMES` | Khung mất trước khi EXPIRED, mặc định `2` |
| `RAIN_CELL_FRAME_COUNT` | Số khung radar past xử lý, mặc định `4` |
| `RAIN_CELL_BUFFER_KM` | Buffer hành lang quanh route, mặc định `50` |
| `RAIN_CELL_TILE_ZOOM` | Zoom tile decode (≤7), mặc định `5` |
| `ROUTE_WEATHER_SAMPLE_INTERVAL_KM` | Khoảng cách mẫu mục tiêu (km), mặc định `10` |
| `ROUTE_WEATHER_MIN_POINTS` | Số điểm tối thiểu, mặc định `5` |
| `ROUTE_WEATHER_MAX_POINTS` | Số điểm tối đa (chống nổ request), mặc định `20` |
| `CORS_ORIGINS` | Origin frontend được phép |
| `NUXT_PUBLIC_API_BASE_URL` | URL backend cho frontend |
| `NUXT_PUBLIC_MAP_STYLE_URL` | MapLibre style URL |

Không commit credentials thật.

## Cách tính route weather

1. Geocode / chọn origin–destination  
2. GraphHopper → geometry, distance, duration  
3. Sample điểm: `ceil(distance_km / interval) + 1`, clamp `[MIN, MAX]`, luôn gồm 2 đầu  
4. ETA từng điểm theo tỉ lệ quãng đường + giờ xuất phát  
5. Weather từng điểm tại ETA (Open-Meteo → `WeatherSnapshot`)  
6. UI: map + summary + timeline; `weather_status` = `ok` | `partial` | `unavailable`

## API

| Method | Path | Mô tả |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/geocode` | Autocomplete địa chỉ |
| POST | `/api/route-weather` | Route + weather (single compute) |
| GET | `/api/radar/current` | Metadata radar hiện tại (tile URL, timestamp) |
| GET | `/api/satellite/latest` | Metadata ảnh vệ tinh hiện tại (tile URL, timestamp) |
| POST | `/api/rain-cells/track` | Detect + track vùng mưa trong hành lang lộ trình |
| POST | `/api/nowcasting/predict` | Dự báo vị trí vùng mưa 5–60 phút (baseline extrapolation) |
| POST | `/api/traffic/prediction` | Giao thông hiện tại + dự báo 5–30 phút (baseline + weather impact) |
| POST | `/api/weather-fusion/state` | Unified multi-source weather state theo route segment |
| POST | `/api/route-weather/compare` | So sánh giờ xuất phát (backend; UI Stage 1 không dùng) |

## Known limitations

- Rain-cell detection dùng tile RainViewer scheme 0 (grayscale proxy), độ phân giải phụ thuộc zoom/buffer
- Baseline detector có thể nhầm clutter/nhiễu; không phải storm-cell typing chuyên môn
- Radar RainViewer: độ phân giải ~1 km, cập nhật ~5–10 phút; tile chỉ có đến **zoom 7** (map zoom sâu hơn sẽ scale tile, không request z>7)
- RainViewer free tier: attribution bắt buộc, không dùng cho sản phẩm thương mại trả phí (xem [Terms](https://www.rainviewer.com/terms.html))
- Open-Meteo độ phân giải theo giờ
- GraphHopper free tier giới hạn credit / non-commercial
- ETA chưa tính traffic
- Geocoding đường nhỏ ở VN có thể lệch
- Dự báo mang tính xác suất
- Satellite Stage 4 fuse theo metadata thời gian/chất lượng/provenance; chưa decode pixel ảnh vệ tinh (feature hiện tại lấy từ forecast + rain-cell + timestamp)
- Conflict radar-satellite dùng deterministic threshold, không tự quyết định nguồn nào “đúng” hơn
- Nowcasting Stage 5 là baseline extrapolation (`baseline` / `0.1`), không phải ML đã train; confidence giảm theo horizon; thiếu vận tốc thì giữ vị trí; không thay thế radar quan sát
- Traffic Stage 6 dùng `SyntheticTrafficProvider` — giao thông demo/heuristic, **không phải** live traffic; baseline trend + rule-based weather impact; nowcast được gọi nội bộ backend

## Roadmap

- [x] Stage 1 — Route Weather MVP
- [x] Stage 2 — Live Radar
- [x] Stage 3 — Rain-cell Detection & Tracking
- [x] Stage 4 — Satellite + Data Fusion
- [x] Stage 5 — AI Nowcasting
- [x] Stage 6 — Traffic Prediction
- [ ] Stage 7 — Route Weather Intelligence

## Tài liệu

- [Design Spec Stage 1](docs/superpowers/specs/2026-08-21-route-weather-stage1-design.md)
- [Design Spec Stage 3](docs/superpowers/specs/2026-08-24-stage3-rain-cell-tracking-design.md)
- [Design Spec Stage 5](docs/superpowers/specs/2026-08-25-stage5-ai-nowcasting-design.md)
- [Design Spec Stage 6](docs/superpowers/specs/2026-08-25-stage6-traffic-prediction-design.md)
- [Implementation Plan](docs/superpowers/plans/2026-08-21-route-weather-stage1.md)

## Stage 4 — Satellite + Multi-source Data Fusion

Stage 4 tích hợp dữ liệu vệ tinh và thêm lớp fusion deterministic để tạo trạng thái thời tiết hợp nhất theo route segment, có temporal alignment, freshness và provenance.

Implemented:
- satellite integration (NASA GIBS Himawari WMTS) qua adapter/service riêng
- satellite map layer độc lập, bật/tắt riêng, chỉnh opacity
- timestamp/freshness tracking cho radar, satellite, forecast, rain cells
- source provenance preservation trong unified weather state
- normalized weather state + deterministic fusion engine
- data quality metadata (`GOOD`, `STALE`, `MISSING`, `CONFLICTING`, `UNKNOWN`)
- route-oriented fused weather state (`/api/weather-fusion/state`)
- corridor overlap: rain-cell gán vào segment gần nhất nếu nằm trong `FUSION_CORRIDOR_KM` (không dùng midpoint 50 km)
- per-segment confidence (0–1) từ freshness/quality/conflict
- deterministic nowcast features trên từng segment (`precip_evidence`, age, overlap, …) cho Stage 5
- fusion debug panel (dev / `NUXT_PUBLIC_ENABLE_FUSION_DEBUG=true`)

Not implemented:
- trained ML / deep learning (Stage 5 chỉ baseline extrapolation)
- live traffic provider (Stage 6 dùng synthetic baseline)
- final route risk engine

## Stage 5 — AI Nowcasting (baseline)

Stage 5 trả lời: vùng mưa đang theo dõi sẽ **có thể** ở đâu trong 5–60 phút tới. Pipeline: tracking Stage 3 → `NowcastingEngine` → `BaselineExtrapolationModel` (`name=baseline`, `version=0.1`) → API + lớp predicted trên map.

Đây **không phải** mô hình ML/DL đã train — chỉ extrapolation chuyển động (tốc độ/hướng quan sát). Chỗ cắm model sau không đổi API/UI.

```text
Route geometry
  → POST /api/nowcasting/predict
  → NowcastingService
  → RainCellService.track_for_route   ← Stage 3 reuse
  → NowcastingEngine
  → BaselineExtrapolationModel (v0.1)
  → useNowcasting → RouteMap (predicted layers) + timeline NOW/+5m…/+60m
```

**Có thêm:**
- `POST /api/nowcasting/predict` với `{ geometry, buffer_km? }`
- Toggle **Nowcasting (dự báo mưa)** và timeline `NOW / +5m / +10m / +15m / +30m / +60m`
- Lớp predicted riêng (teal, dashed) — không vẽ như radar quan sát

**Giới hạn baseline:** tuyến tính theo vận tốc hiện tại; thiếu vận tốc thì giữ vị trí + confidence thấp; horizon càng xa càng kém tin cậy; không storm-cell typing, không route-risk.

### Cách test local

Backend:

```bash
cd backend
python -m pytest tests/test_geo_math_destination.py tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py tests/test_rain_cells.py tests/test_fusion_engine.py -v
```

UI: phân tích lộ trình → bật **Nowcasting (dự báo mưa)** → chọn `+5m`…`+60m` để xem vùng mưa dự báo. `NOW` chỉ hiện lớp quan sát (radar / rain cells). Nút **Làm mới** cũng refresh nowcast khi toggle đang bật.

## Stage 6 — Traffic Prediction (baseline)

Stage 6 trả lời: trên lộ trình này, giao thông **hiện tại** và **có thể** thay đổi thế nào trong 5–30 phút tới khi kết hợp baseline traffic + tác động mưa dự báo (nowcast Stage 5 gọi nội bộ backend).

Đây **không phải** live traffic hay mô hình ML đã train — `SyntheticTrafficProvider` tạo dữ liệu demo deterministic; `BaselineTrafficModel` + `WeatherImpactModel` rule-based. Thiết kế modular để sau này cắm provider live / ML mà không đổi API/UI.

```text
Route geometry (client)
  → POST /api/traffic/prediction
  → TrafficService
  → SyntheticTrafficProvider → RoadSegment[] + TrafficState (current)
  → BaselineTrafficModel → base prediction per segment × horizon
  → NowcastingEngine (Stage 5 reuse, internal)
  → WeatherImpactModel → weather impact per segment × horizon
  → TrafficPredictionEngine.combine
  → useTraffic → RouteMap (traffic layers) + timeline NOW/+5m…/+30m
```

**Có thêm:**
- `POST /api/traffic/prediction` với `{ geometry, buffer_km? }`
- Toggle **Giao thông** (current) và **Dự báo giao thông** (predicted)
- Timeline traffic độc lập: `NOW / +5m / +10m / +15m / +30m` (không +60m)
- Lớp segment trên map (màu theo congestion); predicted dashed; click popup giải thích segment
- Disclaimer: giao thông synthetic, không phải live

**Giới hạn baseline:** heuristic time-of-day + synthetic speeds; weather impact rule-based từ nowcast; confidence giảm theo horizon; không traffic-aware ETA; không route-risk scoring.

### Cách test local

Backend:

```bash
cd backend
python -m pytest tests/test_traffic_state.py tests/test_traffic_synthetic.py tests/test_traffic_baseline.py tests/test_weather_impact.py tests/test_traffic_engine.py tests/test_traffic_api.py tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py tests/test_rain_cells.py tests/test_fusion_engine.py -v
```

UI: phân tích lộ trình → bật **Giao thông** để xem tắc đường hiện tại (NOW) → bật **Dự báo giao thông** → chọn `+5m`…`+30m` để xem segment dự báo. Nút **Làm mới** cũng refresh traffic khi toggle đang bật.
