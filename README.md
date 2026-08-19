# Route Weather

Ứng dụng lập kế hoạch lộ trình kèm dự báo thời tiết theo không gian và thời gian.

> "Nếu tôi đi từ A đến B lúc X giờ, tôi sẽ gặp thời tiết gì trên đường?"

## Tech Stack

- **Frontend:** Nuxt 4, Vue 3, TypeScript, Tailwind CSS, Pinia, MapLibre GL JS
- **Backend:** Python, FastAPI
- **Database:** PostgreSQL (cache)
- **Routing/Geocoding:** GraphHopper Cloud
- **Weather:** Open-Meteo

## Yêu cầu

- Docker & Docker Compose
- Node.js 20+ (dev local frontend, tùy chọn)
- Python 3.12+ (dev local backend, tùy chọn)

## Bắt đầu nhanh

### 1. Cấu hình môi trường

```bash
cp .env.example .env
```

Thêm `GRAPHHOPPER_API_KEY` vào `.env` (đăng ký miễn phí tại [graphhopper.com](https://www.graphhopper.com) — không cần thẻ tín dụng).

### 2. Chạy với Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

### 3. Dev local (không Docker)

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

## Cấu trúc dự án

```
route-weather/
├── frontend/          # Nuxt 4 app
├── backend/           # FastAPI app
├── docs/              # Design specs & plans
├── docker-compose.yml
└── .env.example
```

## API Endpoints (planned)

| Method | Path | Mô tả |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/route-weather` | Tính lộ trình + thời tiết |
| POST | `/api/route-weather/compare` | So sánh giờ xuất phát |
| GET | `/api/geocode` | Autocomplete địa chỉ |

## Tài liệu

- [Design Spec](docs/superpowers/specs/2026-08-19-route-weather-design.md)
- [Implementation Plan](docs/superpowers/plans/2026-08-19-route-weather.md)
