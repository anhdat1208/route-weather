### Task 3: BaselineTrafficModel

**Files:**
- Create: `backend/app/engine/traffic_models.py`
- Create: `backend/tests/test_traffic_baseline.py`

**Interfaces:**
- Consumes: `RoadSegmentOut`, `tod_factor` (import from synthetic provider **or** extract `tod_factor` into `engine/traffic_tod.py` if needed to avoid circular imports â€” **prefer extract** `tod_factor` + `hour_weekday` into `backend/app/engine/traffic_tod.py` used by both synthetic provider and baseline). If Task 2 already inlined `tod_factor` in the provider, **move** it to `traffic_tod.py` in this task and update the provider import.
- Produces:
  - `class TrafficPredictionModel(Protocol): name: str; version: str; def predict_base(self, segments, *, at: datetime, horizons: list[int]) -> list[tuple[str, int, SpeedCongestionPair]]: ...`
  - `class BaselineTrafficModel` with `name="baseline"`, `version="0.1"` (read from settings)

**Algorithm (lock):**

```text
For each segment, each horizon h:
  current = traffic.current_speed_kmh  (if None: use free_flow, mark missing_current)
  free = traffic.free_flow_speed_kmh
  expected_now = clamp(free * tod_factor(at), free)     # ignore index variation
  expected_future = clamp(free * tod_factor(at + h minutes), free)
  # drift 40% of the way from current toward expected_future (no invented history)
  base_speed = clamp(current + 0.40 * (expected_future - current), free)
  speed_delta_pct = (base_speed / current) - 1   if current > 0 else 0
  congestion from relative(base_speed, free)
```

No history list in Stage 6 synthetic â†’ do not invent trend beyond ToD drift.

- [ ] **Step 1: Write failing tests**

```python
from __future__ import annotations

from datetime import datetime, timezone

from app.engine.traffic_models import BaselineTrafficModel
from app.providers.synthetic_traffic import SyntheticTrafficProvider
from app.schemas.common import LatLng

GEOM = [LatLng(lat=10.70, lng=106.65), LatLng(lat=10.85, lng=106.80)]


def test_baseline_emits_all_horizons():
    at = datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)
    segs = SyntheticTrafficProvider().current_for_route(GEOM, at=at)
    model = BaselineTrafficModel()
    out = model.predict_base(segs, at=at, horizons=[5, 10, 15, 30])
    keys = {(sid, h) for sid, h, _ in out}
    assert len(segs) * 4 == len(out)
    assert (segs[0].id, 5) in keys and (segs[0].id, 30) in keys
    assert model.name == "baseline" and model.version == "0.1"


def test_baseline_speed_within_clamp():
    at = datetime(2026, 8, 25, 2, 0, tzinfo=timezone.utc)
    segs = SyntheticTrafficProvider().current_for_route(GEOM, at=at)
    pair = BaselineTrafficModel().predict_base(segs, at=at, horizons=[15])[0][2]
    free = segs[0].traffic.free_flow_speed_kmh
    assert pair.speed_kmh is not None
    assert 0.20 * free - 1e-6 <= pair.speed_kmh <= 1.05 * free + 1e-6
```

- [ ] **Step 2: Run â€” expect fail**

- [ ] **Step 3: Implement `traffic_tod.py` + `BaselineTrafficModel`**

`predict_base` return type: `list[tuple[str, int, SpeedCongestionPair]]` (segment_id, horizon, pair). Skip segments with `traffic is None`.

- [ ] **Step 4: Tests pass** (include synthetic tests still)

- [ ] **Step 5: Commit**

Message: `feat(traffic): add baseline traffic prediction model`

---

