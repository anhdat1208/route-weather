### Task 1: Config, schemas, congestion helpers

**Files:**
- Modify: `backend/app/config.py`
- Create: `backend/app/schemas/traffic.py`
- Create: `backend/app/engine/traffic_state.py`
- Create: `backend/tests/test_traffic_state.py`

**Interfaces:**
- Produces:
  - Settings fields listed in Step 3
  - `congestion_from_relative(relative: float | None) -> CongestionLevel | None`
  - `relative_speed(current: float | None, free_flow: float | None) -> float | None`
  - `clamp_speed(speed: float, free_flow: float | None) -> float`
  - Schemas: `TrafficPredictRequest`, `TrafficStateOut`, `RoadSegmentOut`, `TrafficPredictionOut`, `TrafficPredictionResponse`, `WeatherImpactInfo`, `SpeedCongestionPair`, `TrafficModelInfo`

- [ ] **Step 1: Write failing congestion tests**

Create `backend/tests/test_traffic_state.py`:

```python
from __future__ import annotations

from app.engine.traffic_state import (
    clamp_speed,
    congestion_from_relative,
    relative_speed,
)


def test_relative_speed_and_none():
    assert relative_speed(40.0, 40.0) == 1.0
    assert abs(relative_speed(20.0, 40.0) - 0.5) < 1e-9
    assert relative_speed(None, 40.0) is None
    assert relative_speed(20.0, 0.0) is None


def test_congestion_bands():
    assert congestion_from_relative(0.95) == "free"
    assert congestion_from_relative(0.80) == "slow"
    assert congestion_from_relative(0.60) == "moderate"
    assert congestion_from_relative(0.40) == "heavy"
    assert congestion_from_relative(0.20) == "severe"
    assert congestion_from_relative(None) is None


def test_clamp_speed_band():
    assert clamp_speed(50.0, 40.0) == 42.0  # 1.05 * free_flow
    assert clamp_speed(2.0, 40.0) == 8.0    # 0.20 * free_flow floor
    assert clamp_speed(30.0, None) == 30.0
```

- [ ] **Step 2: Run test â€” expect fail**

Run: `cd backend; python -m pytest tests/test_traffic_state.py -v`  
Expected: FAIL `ImportError` / module missing

- [ ] **Step 3: Implement helpers + config + schemas**

Create `backend/app/engine/traffic_state.py`:

```python
from __future__ import annotations

from typing import Literal

CongestionLevel = Literal["free", "slow", "moderate", "heavy", "severe"]

# relative = current / free_flow
_FREE = 0.85
_SLOW = 0.70
_MODERATE = 0.50
_HEAVY = 0.30
_MAX_VS_FREE = 1.05
_MIN_VS_FREE = 0.20


def relative_speed(current: float | None, free_flow: float | None) -> float | None:
    if current is None or free_flow is None or free_flow <= 0:
        return None
    return current / free_flow


def congestion_from_relative(relative: float | None) -> CongestionLevel | None:
    if relative is None:
        return None
    if relative >= _FREE:
        return "free"
    if relative >= _SLOW:
        return "slow"
    if relative >= _MODERATE:
        return "moderate"
    if relative >= _HEAVY:
        return "heavy"
    return "severe"


def clamp_speed(speed: float, free_flow: float | None) -> float:
    if free_flow is None or free_flow <= 0:
        return max(0.0, speed)
    return max(free_flow * _MIN_VS_FREE, min(free_flow * _MAX_VS_FREE, speed))
```

Append to `Settings` in `backend/app/config.py`:

```python
    traffic_model_name: str = "baseline"
    traffic_model_version: str = "0.1"
    traffic_horizons_minutes: list[int] = [5, 10, 15, 30]
    traffic_sample_interval_km: float = 5.0
    traffic_sample_min_points: int = 3
    traffic_sample_max_points: int = 24
    traffic_free_flow_default_kmh: float = 40.0
    traffic_stale_after_seconds: int = 900
    traffic_rain_nearby_km: float = 8.0
    traffic_base_confidence: float = 0.75
```

Create `backend/app/schemas/traffic.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import LatLng

TrafficStatus = Literal["ok", "partial", "unavailable"]
NowcastEmbedStatus = Literal["ok", "partial", "unavailable", "skipped"]
CongestionLevel = Literal["free", "slow", "moderate", "heavy", "severe"]
WeatherImpactLevel = Literal["none", "low", "moderate", "high"]
RoadType = Literal["arterial", "local", "unknown"]


class TrafficPredictRequest(BaseModel):
    geometry: list[LatLng] = Field(..., min_length=2)
    buffer_km: float | None = Field(default=None, ge=1, le=300)


class TrafficModelInfo(BaseModel):
    name: str
    version: str


class TrafficStateOut(BaseModel):
    current_speed_kmh: float | None = None
    free_flow_speed_kmh: float | None = None
    congestion_level: CongestionLevel | None = None
    relative_speed: float | None = None
    timestamp: datetime
    source: str
    stale: bool = False


class RoadSegmentOut(BaseModel):
    id: str
    geometry: list[LatLng]
    road_type: str | None = None
    name: str | None = None
    traffic: TrafficStateOut | None = None


class SpeedCongestionPair(BaseModel):
    speed_kmh: float | None = None
    congestion: CongestionLevel | None = None
    speed_delta_pct: float | None = None


class WeatherImpactInfo(BaseModel):
    speed_delta_pct: float
    level: WeatherImpactLevel
    rain_probability: float | None = Field(default=None, ge=0, le=1)
    rain_intensity: float | None = None
    reasons: list[str] = Field(default_factory=list)


class TrafficPredictionOut(BaseModel):
    road_segment_id: str
    forecast_minutes: int
    predicted_speed_kmh: float | None = None
    predicted_congestion: CongestionLevel | None = None
    confidence: float = Field(..., ge=0, le=1)
    base_prediction: SpeedCongestionPair
    weather_impact: WeatherImpactInfo
    weather_adjusted: SpeedCongestionPair
    model: TrafficModelInfo


class TrafficPredictionResponse(BaseModel):
    generated_at: datetime
    status: TrafficStatus
    model: TrafficModelInfo
    horizons: list[int]
    segments: list[RoadSegmentOut]
    predictions: list[TrafficPredictionOut]
    nowcast_status: NowcastEmbedStatus
    message: str | None = None
```

- [ ] **Step 4: Re-run tests â€” expect pass**

Run: `cd backend; python -m pytest tests/test_traffic_state.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

Message: `feat(traffic): add schemas and congestion helpers`

---

