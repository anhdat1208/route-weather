### Task 2: BaselineExtrapolationModel (TDD core)

**Files:**
- Create: `backend/app/engine/nowcasting_models.py`
- Create: `backend/tests/test_nowcasting_baseline.py`

**Interfaces:**
- Consumes: `TrackedRainCellOut`, `destination_point`, settings horizons / intensity max
- Produces:
  - `class NowcastingModel(Protocol): def predict(self, cells, *, frames_used: int, radar_age_seconds: int | None, horizons: list[int]) -> list[PredictedRainCell]`
  - `class BaselineExtrapolationModel: ...` with `name`/`version` properties
  - Helpers used by tests: intensity trend, confidence decay (can be module-private)

**Algorithm locked by tests:**
- Eligible states: `TRACKING`, `NEW` only
- Distance km = `speed_kmh * (forecast_minutes / 60)`
- Missing speed or bearing â†’ hold centroid/bounds; confidence â‰¤ 0.35 for that cell-horizon
- Intensity: linear slope from history means if â‰¥2 samples; else current mean; clamp `[0, nowcast_intensity_max]`
- `rain_probability = clamp(intensity / nowcast_intensity_max, 0, 1)` (None if intensity None)
- Confidence base = `motion.confidence` or `0.4`; multiply by horizon factor `max(0.25, 1 - forecast_minutes/90)`; Ã—0.7 if `frames_used < nowcast_min_frames_for_full_confidence`; Ã—0.75 if `len(history) < 2`; Ã—0.5 if missing motion vector; if `radar_age_seconds` and `> settings.radar_stale_after_seconds` Ã—0.6

- [ ] **Step 1: Write failing baseline tests**

Create `backend/tests/test_nowcasting_baseline.py` with fixtures building `TrackedRainCellOut` + `CellMotionOut` + history. Cover at minimum:

```python
def test_horizons_emit_five_predictions_per_cell():
    ...
    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=[5, 10, 15, 30, 60])
    assert sorted({p.forecast_minutes for p in preds}) == [5, 10, 15, 30, 60]
    assert all(p.kind == "predicted" for p in preds)
    assert all(p.cell_id == "c1" for p in preds)


def test_projects_centroid_with_speed_and_bearing():
    # speed 60 km/h east â†’ +5 min â‰ˆ 5 km east
    ...


def test_missing_velocity_holds_position_low_confidence():
    ...


def test_missing_direction_holds_position_low_confidence():
    ...


def test_intensity_extrapolates_from_history():
    ...


def test_intensity_fallback_without_history():
    ...


def test_confidence_decreases_with_horizon():
    confs = [p.confidence for p in preds if p.cell_id == "c1"]
    assert confs == sorted(confs, reverse=True)


def test_stale_radar_reduces_confidence():
    ...


def test_short_history_reduces_confidence():
    ...


def test_lost_cells_omitted():
    ...


def test_no_cells_returns_empty():
    assert model.predict([], frames_used=3, radar_age_seconds=60, horizons=[5, 10, 15, 30, 60]) == []
```

Use `haversine_distance_m` assertions (Â±500 m tolerance for 5 km projection).

- [ ] **Step 2: Run tests â€” expect fail**

Run: `cd backend; python -m pytest tests/test_nowcasting_baseline.py -v`  
Expected: FAIL import / missing module

- [ ] **Step 3: Implement `nowcasting_models.py`**

Implement protocol + `BaselineExtrapolationModel` exactly matching the algorithm above. Translate bounds by the same lat/lng delta as centroid when bounds exist. Set `source="rain_cell_track+baseline"`, `motion` from input speed/bearing used.

- [ ] **Step 4: Run tests â€” expect pass**

Run: `cd backend; python -m pytest tests/test_nowcasting_baseline.py -v`  
Expected: all PASS

- [ ] **Step 5: Commit**

Message: `feat(nowcast): add baseline extrapolation model`

---
