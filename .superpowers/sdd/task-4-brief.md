### Task 4: Service + API + main registration

**Files:**
- Create: `backend/app/services/nowcasting_service.py`
- Create: `backend/app/api/nowcasting.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_nowcasting_api.py`

**Interfaces:**
- `NowcastingService.predict_for_route(geometry, buffer_km=None) -> NowcastPredictionResponse`
- Internally: `track = await get_rain_cell_service().track_for_route(...)` then `return run_nowcast(track)`
- `get_nowcasting_service()` singleton like rain cells
- Router: `@router.post("/api/nowcasting/predict", response_model=NowcastPredictionResponse)`

- [ ] **Step 1: Write API test with mocked nowcasting service**

Mirror `test_rain_cells_api.py`: patch `app.services.nowcasting_service._nowcasting_service` with `AsyncMock` returning a filled `NowcastPredictionResponse`, POST geometry, assert 200 + `model.name == "baseline"` + horizons + `predictions[0].kind == "predicted"`.

Also add one unit-style test that `NowcastingService.predict_for_route` calls rain-cell track then engine (mock `get_rain_cell_service`).

- [ ] **Step 2: Run â€” expect fail**

- [ ] **Step 3: Implement service + API; register in `main.py`**

In `main.py`, inside the successful boot block, after rain-cells try/except, add similar:

```python
    try:
        from app.api.nowcasting import router as nowcasting_router
        app.include_router(nowcasting_router)
    except Exception:
        logging.getLogger(__name__).exception("Nowcasting router failed to load")
```

- [ ] **Step 4: Run API + engine + baseline suite**

Run: `cd backend; python -m pytest tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py -v`  
Expected: all PASS

- [ ] **Step 5: Commit**

Message: `feat(nowcast): expose POST /api/nowcasting/predict`

---
