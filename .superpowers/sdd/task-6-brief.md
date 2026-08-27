### Task 6: TrafficService + API

**Files:**
- Create: `backend/app/services/traffic_service.py`
- Create: `backend/app/api/traffic.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_traffic_api.py`

**Interfaces:**
- `TrafficService.predict_for_route(geometry, buffer_km=None)`:
  1. `segments = SyntheticTrafficProvider().current_for_route(geometry)`
  2. Try `await get_nowcasting_service().predict_for_route(geometry, buffer_km=buffer_km)`. On exception: treat as nowcast unavailable (`NowcastPredictionResponse` with status unavailable, empty predictions) â€” **do not** fail the whole traffic request.
  3. Return `run_traffic_prediction(segments, nowcast=..., at=now)`
- Router: `POST /api/traffic/prediction` like nowcasting
- `main.py`: isolated `try/except` include (copy nowcasting pattern, log `"Traffic router failed to load"`)

- [ ] **Step 1: Write API test with mocked traffic service** (same pattern as `test_nowcasting_predict_endpoint_with_mock_service` swapping module `_traffic_service`)

Also add a service-level test (can live in same file) that mocks `get_nowcasting_service` to raise / return unavailable and asserts traffic status still ok with empty weather impact.

- [ ] **Step 2: Run â€” expect fail**

- [ ] **Step 3: Implement service, API, register router**

`get_traffic_service()` singleton like nowcasting.

- [ ] **Step 4: Tests pass**

Run: `cd backend; python -m pytest tests/test_traffic_api.py tests/test_traffic_engine.py tests/test_nowcasting_api.py -v`

- [ ] **Step 5: Commit**

Message: `feat(traffic): expose POST /api/traffic/prediction`

---

