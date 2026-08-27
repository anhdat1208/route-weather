### Task 2: TrafficProvider + SyntheticTrafficProvider

**Files:**
- Modify: `backend/app/providers/base.py`
- Create: `backend/app/providers/synthetic_traffic.py`
- Create: `backend/tests/test_traffic_synthetic.py`

**Interfaces:**
- Consumes: `sample_points_by_distance`, `TrafficStateOut`, `RoadSegmentOut`, settings
- Produces:
  - `class TrafficProvider(Protocol): def current_for_route(self, geometry: list[LatLng], *, at: datetime | None = None) -> list[RoadSegmentOut]: ...`
  - `SyntheticTrafficProvider.current_for_route(...)`

**ToD curve (lock this formula â€” tests depend on it):**

```text
tod_factor(hour, weekday):
  weekday 0â€“4 (Monâ€“Fri):
    hour in [7, 8] or [17, 18] â†’ 0.70
    hour in [6, 9, 16, 19] â†’ 0.82
    else â†’ 0.95
  weekend:
    hour in [10, 11, 12, 17, 18] â†’ 0.88
    else â†’ 0.98
current = clamp(free_flow * tod_factor * (1 - 0.04 * (index % 5)), free_flow)
```

Always `source="synthetic"`, `stale=False` for freshly built snapshots. `road_type="unknown"`. `id=f"route-seg-{i}"`. Geometry = `[samples[i].point, samples[i+1].point]` (N samples â†’ N-1 segments).

- [ ] **Step 1: Write failing synthetic tests**

```python
from __future__ import annotations

from datetime import datetime, timezone

from app.providers.synthetic_traffic import SyntheticTrafficProvider
from app.schemas.common import LatLng


GEOM = [LatLng(lat=10.70, lng=106.65), LatLng(lat=10.85, lng=106.80)]


def test_synthetic_builds_labeled_segments():
    segs = SyntheticTrafficProvider().current_for_route(
        GEOM, at=datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)  # Tue 08:00 UTC
    )
    assert len(segs) >= 1
    assert segs[0].id == "route-seg-0"
    assert segs[0].traffic is not None
    assert segs[0].traffic.source == "synthetic"
    assert segs[0].traffic.stale is False
    assert segs[0].traffic.congestion_level is not None
    assert len(segs[0].geometry) == 2


def test_synthetic_rush_hour_slower_than_night():
    p = SyntheticTrafficProvider()
    rush = p.current_for_route(GEOM, at=datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc))
    night = p.current_for_route(GEOM, at=datetime(2026, 8, 25, 2, 0, tzinfo=timezone.utc))
    assert rush[0].traffic.current_speed_kmh < night[0].traffic.current_speed_kmh


def test_synthetic_same_timestamp_is_deterministic():
    p = SyntheticTrafficProvider()
    at = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
    a = p.current_for_route(GEOM, at=at)
    b = p.current_for_route(GEOM, at=at)
    assert a[0].traffic.current_speed_kmh == b[0].traffic.current_speed_kmh
```

- [ ] **Step 2: Run â€” expect fail**

Run: `cd backend; python -m pytest tests/test_traffic_synthetic.py -v`

- [ ] **Step 3: Implement Protocol + provider**

Add to `backend/app/providers/base.py`:

```python
from datetime import datetime
from app.schemas.traffic import RoadSegmentOut

class TrafficProvider(Protocol):
    def current_for_route(
        self,
        geometry: list[LatLng],
        *,
        at: datetime | None = None,
    ) -> list[RoadSegmentOut]:
        ...
```

Create `backend/app/providers/synthetic_traffic.py` implementing `tod_factor` and `current_for_route` as specified. Use `sample_points_by_distance` with `interval_km=settings.traffic_sample_interval_km`, `min_points=settings.traffic_sample_min_points`, `max_points=settings.traffic_sample_max_points`. Fill `TrafficStateOut` via `relative_speed` + `congestion_from_relative` + `clamp_speed`. `timestamp=at` (default `datetime.now(timezone.utc)`).

- [ ] **Step 4: Tests pass**

Run: `cd backend; python -m pytest tests/test_traffic_synthetic.py tests/test_traffic_state.py -v`

- [ ] **Step 5: Commit**

Message: `feat(traffic): add synthetic traffic provider`

---

