# Route Weather

Ứng dụng lập kế hoạch lộ trình kèm dự báo thời tiết theo không gian và thời gian.

> "Nếu tôi đi từ A đến B, tôi sẽ gặp thời tiết gì trên đường và lúc nào?"

## Stage 1 scope

**Có:** nhập origin/destination (+ phương tiện, giờ xuất phát), tính route trên map, sampling điểm theo interval cấu hình được, ETA từng điểm, weather normalized qua adapter, timeline thời tiết, loading/error, weather fail không làm mất route.

**Không có (giai đoạn sau):** radar, satellite, rain-cell tracking, AI nowcasting, traffic prediction, risk scoring trên UI.

## Tech Stack

- **Frontend:** Nuxt 4, Vue 3, TypeScript, Tailwind CSS, MapLibre GL JS
- **Backend:** Python 3.12, FastAPI
- **Routing/Geocoding:** GraphHopper Cloud
- **Weather:** Open-Meteo (normalized → internal model → UI)

## Architecture

```text
User → RouteForm
         ↓
  useRouteWeather
         ↓
  POST /api/route-weather
         ↓
  RouteWeatherEngine
   ├── GraphHopper (route + geocode)
   ├── Sampler (interval km + min/max)
   ├── ETA
   └── Open-Meteo → WeatherSnapshot
         ↓
  RouteMap + JourneySummary + WeatherTimeline
```

Map layers (Stage 1): Base → Route → Weather points. Stubs sẵn cho radar / satellite / rain-cell / traffic.

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
| POST | `/api/route-weather/compare` | So sánh giờ xuất phát (backend; UI Stage 1 không dùng) |

## Known limitations

- Open-Meteo độ phân giải theo giờ
- GraphHopper free tier giới hạn credit / non-commercial
- ETA chưa tính traffic
- Geocoding đường nhỏ ở VN có thể lệch
- Dự báo mang tính xác suất

## Roadmap

- [x] Stage 1 — Route Weather MVP
- [ ] Stage 2 — Live Radar
- [ ] Stage 3 — Rain-cell Tracking
- [ ] Stage 4 — Satellite + Data Fusion
- [ ] Stage 5 — AI Nowcasting
- [ ] Stage 6 — Traffic Prediction
- [ ] Stage 7 — Route Weather Intelligence

## Tài liệu

- [Design Spec](docs/superpowers/specs/2026-08-21-route-weather-stage1-design.md)
- [Implementation Plan](docs/superpowers/plans/2026-08-21-route-weather-stage1.md)
