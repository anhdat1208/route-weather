### Task 8: Wire `index.vue` + README

**Files:**
- Modify: `frontend/app/pages/index.vue`
- Modify: `README.md`

**Wiring:**
- Import `useNowcasting`
- On analyze success / geometry available: if nowcasting enabled, `fetchNowcast(geometry)` (same geometry as rain cells)
- Pass props to `RadarControls` and `RouteMap`
- `onRefreshLayers` also refreshes nowcast when enabled
- README: Stage 5 section describing baseline architecture diagram (short), how to call API, how to toggle UI; mark roadmap `[x] Stage 5` only after feature works â€” during this task set to `[x]` and note baseline limitations

- [ ] **Step 1: Wire page**

- [ ] **Step 2: Update README Stage 5**

Include:
- Architecture one-liner matching spec
- `POST /api/nowcasting/predict`
- Baseline â‰  trained ML
- How to test locally (backend pytest + UI toggle)

- [ ] **Step 3: Run full backend nowcast-related tests**

Run: `cd backend; python -m pytest tests/test_geo_math_destination.py tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py tests/test_rain_cells.py tests/test_fusion_engine.py -v`  
Expected: all PASS (Stage 3/4 unbroken)

- [ ] **Step 4: Commit**

Message: `feat(nowcast): wire Stage 5 UI and document baseline nowcasting`

---
