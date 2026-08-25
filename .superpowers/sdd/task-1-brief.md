### Task 1: Geo helper + config + schemas

**Files:**
- Modify: `backend/app/engine/geo_math.py`
- Modify: `backend/app/config.py`
- Create: `backend/app/schemas/nowcasting.py`
- Create: `backend/tests/test_geo_math_destination.py`

**Interfaces:**
- Produces:
  - `destination_point(origin: LatLng, distance_km: float, bearing_degrees: float) -> LatLng`
  - Settings: `nowcast_model_name: str = "baseline"`, `nowcast_model_version: str = "0.1"`, `nowcast_horizons_minutes: list[int]` default `[5,10,15,30,60]`, `nowcast_intensity_max: float = 255.0`, `nowcast_min_frames_for_full_confidence: int = 3`
  - Schemas: `NowcastPredictRequest`, `NowcastModelInfo`, `PredictedCellMotion`, `PredictedRainCell`, `NowcastPredictionResponse`

- [ ] **Step 1: Write failing destination_point test**

Create `backend/tests/test_geo_math_destination.py`:

```python
from __future__ import annotations

from app.engine.geo_math import destination_point, haversine_distance_m
from app.schemas.common import LatLng


def test_destination_point_north_1km():
    origin = LatLng(lat=10.0, lng=106.0)
    dest = destination_point(origin, distance_km=1.0, bearing_degrees=0.0)
    dist_m = haversine_distance_m(origin, dest)
    assert abs(dist_m - 1000.0) < 15.0
    assert dest.lat > origin.lat
    assert abs(dest.lng - origin.lng) < 1e-4


def test_destination_point_east_and_zero():
    origin = LatLng(lat=10.0, lng=106.0)
    east = destination_point(origin, distance_km=2.0, bearing_degrees=90.0)
    assert east.lng > origin.lng
    same = destination_point(origin, distance_km=0.0, bearing_degrees=123.0)
    assert same.lat == origin.lat and same.lng == origin.lng
```

- [ ] **Step 2: Run test â€” expect fail**

Run: `cd backend; python -m pytest tests/test_geo_math_destination.py -v`  
Expected: FAIL `ImportError` / `destination_point` missing

- [ ] **Step 3: Implement destination_point + config + schemas**

Add to `geo_math.py`:

```python
def destination_point(origin: LatLng, distance_km: float, bearing_degrees: float) -> LatLng:
    """Move from origin along initial bearing by distance_km (spherical Earth)."""
    if distance_km <= 0:
        return LatLng(lat=origin.lat, lng=origin.lng)
    lat1 = math.radians(origin.lat)
    lng1 = math.radians(origin.lng)
    brng = math.radians(bearing_degrees)
    angular = (distance_km * 1000.0) / EARTH_RADIUS_M
    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular)
        + math.cos(lat1) * math.sin(angular) * math.cos(brng)
    )
    lng2 = lng1 + math.atan2(
        math.sin(brng) * math.sin(angular) * math.cos(lat1),
        math.cos(angular) - math.sin(lat1) * math.sin(lat2),
    )
    return LatLng(lat=math.degrees(lat2), lng=((math.degrees(lng2) + 540) % 360) - 180)
```

Append to `Settings` in `config.py`:

```python
    nowcast_model_name: str = "baseline"
    nowcast_model_version: str = "0.1"
    nowcast_horizons_minutes: list[int] = [5, 10, 15, 30, 60]
    nowcast_intensity_max: float = 255.0
    nowcast_min_frames_for_full_confidence: int = 3
```

Create `backend/app/schemas/nowcasting.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import LatLng
from app.schemas.rain_cell import CellBoundsOut

NowcastStatus = Literal["ok", "partial", "unavailable"]


class NowcastPredictRequest(BaseModel):
    geometry: list[LatLng] = Field(..., min_length=2)
    buffer_km: float | None = Field(default=None, ge=1, le=300)


class NowcastModelInfo(BaseModel):
    name: str
    version: str


class PredictedCellMotion(BaseModel):
    speed_kmh: float | None = None
    bearing_degrees: float | None = None


class PredictedRainCell(BaseModel):
    cell_id: str
    forecast_minutes: int
    kind: Literal["predicted"] = "predicted"
    centroid: LatLng
    bounds: CellBoundsOut | None = None
    rain_probability: float | None = Field(default=None, ge=0, le=1)
    rain_intensity: float | None = None
    confidence: float = Field(..., ge=0, le=1)
    motion: PredictedCellMotion | None = None
    source: str = "rain_cell_track+baseline"


class NowcastPredictionResponse(BaseModel):
    generated_at: datetime
    status: NowcastStatus
    model: NowcastModelInfo
    frames_used: int
    radar_age_seconds: int | None = None
    horizons: list[int]
    predictions: list[PredictedRainCell]
    message: str | None = None
```

- [ ] **Step 4: Re-run destination tests â€” expect pass**

Run: `cd backend; python -m pytest tests/test_geo_math_destination.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/geo_math.py backend/app/config.py backend/app/schemas/nowcasting.py backend/tests/test_geo_math_destination.py
# commit via git.exe -F if wrapper breaks
```

Message: `feat(nowcast): add geo destination helper and nowcasting schemas`

---
