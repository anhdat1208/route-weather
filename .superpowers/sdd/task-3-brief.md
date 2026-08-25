### Task 3: NowcastingEngine

**Files:**
- Create: `backend/app/engine/nowcasting_engine.py`
- Create: `backend/tests/test_nowcasting_engine.py`

**Interfaces:**
- Consumes: `RainCellTrackResponse`, `BaselineExtrapolationModel` (or injected `NowcastingModel`)
- Produces: `def run_nowcast(track: RainCellTrackResponse, *, model: NowcastingModel | None = None, generated_at: datetime | None = None) -> NowcastPredictionResponse`

Status rules:
- `track.status == "unavailable"` â†’ response `unavailable`, predictions `[]`, keep track message (or Vietnamese default)
- `track.status == "partial"` â†’ response `partial` (even if predictions exist)
- Else if any predicted cell has confidence < 0.35 due to missing motion â†’ `partial` with message about incomplete motion
- Else `ok`
- Always set `model` from active model name/version, `horizons` from settings, `frames_used` from track
- `radar_age_seconds`: leave `None` in Stage 5 unless easily derived; engine accepts optional override kwarg default `None`

- [ ] **Step 1: Write engine tests**

```python
def test_engine_unavailable_passthrough():
    ...

def test_engine_empty_cells_ok_with_message():
    # track ok, cells=[] â†’ status ok, predictions=[], message tiáº¿ng Viá»‡t
    ...

def test_engine_runs_baseline_and_sets_model_info():
    ...

def test_engine_partial_when_track_partial():
    ...
```

- [ ] **Step 2: Run â€” expect fail**

- [ ] **Step 3: Implement engine**

```python
def run_nowcast(...):
    model = model or BaselineExtrapolationModel()
    horizons = list(settings.nowcast_horizons_minutes)
    info = NowcastModelInfo(name=model.name, version=model.version)
    if track.status == "unavailable":
        return NowcastPredictionResponse(...)
    preds = model.predict(track.cells, frames_used=track.frames_used, radar_age_seconds=radar_age_seconds, horizons=horizons)
    # status resolution...
```

Expose `name`/`version` properties on baseline model reading from settings.

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

Message: `feat(nowcast): add nowcasting engine orchestrator`

---
