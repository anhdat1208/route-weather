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
         ↓
  RouteMap (Base → Radar → Rain Cells → Route → Weather points)
         +
  RadarControls + JourneySummary + WeatherTimeline
```

Map layers: Base → Radar (Stage 2) → Rain Cells (Stage 3) → Route → Weather points.

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
| POST | `/api/rain-cells/track` | Detect + track vùng mưa trong hành lang lộ trình |
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

## Roadmap

- [x] Stage 1 — Route Weather MVP
- [x] Stage 2 — Live Radar
- [x] Stage 3 — Rain-cell Detection & Tracking
- [ ] Stage 4 — Satellite + Data Fusion
- [ ] Stage 5 — AI Nowcasting
- [ ] Stage 6 — Traffic Prediction
- [ ] Stage 7 — Route Weather Intelligence

## Tài liệu

- [Design Spec Stage 1](docs/superpowers/specs/2026-08-21-route-weather-stage1-design.md)
- [Design Spec Stage 3](docs/superpowers/specs/2026-08-24-stage3-rain-cell-tracking-design.md)
- [Implementation Plan](docs/superpowers/plans/2026-08-21-route-weather-stage1.md)
