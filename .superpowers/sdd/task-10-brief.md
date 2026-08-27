### Task 10: Wire `index.vue` + README + regression tests

**Files:**
- Modify: `frontend/app/pages/index.vue`
- Modify: `README.md`

**Wiring:**
- Import `useTraffic`
- Watch `routeGeometry` + traffic toggles â†’ `fetchTraffic`
- `onRefreshLayers` also refreshes traffic when either toggle on
- Pass new props to `RadarControls` and `RouteMap`
- Do not change nowcast horizon wiring

**README:** new `## Stage 6 â€” Traffic Prediction (baseline)` with pipeline diagram from spec, `POST /api/traffic/prediction`, synthetic disclaimer, how to test. Mark roadmap `[x] Stage 6` only in this task. Link the design spec. Keep Stage 5 section intact.

- [ ] **Step 1: Wire page**

- [ ] **Step 2: Update README**

- [ ] **Step 3: Run backend regression**

Run:

```bash
cd backend
python -m pytest tests/test_traffic_state.py tests/test_traffic_synthetic.py tests/test_traffic_baseline.py tests/test_weather_impact.py tests/test_traffic_engine.py tests/test_traffic_api.py tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py tests/test_rain_cells.py tests/test_fusion_engine.py -v
```

Expected: all PASS

- [ ] **Step 4: Commit**

Message: `feat(traffic): wire Stage 6 UI and document baseline traffic prediction`

---

## Spec coverage checklist (self-review)

| Spec requirement | Task |
|---|---|
| Modular TrafficProvider | 2 |
| RoadSegment from polyline | 2 |
| Synthetic labeled current traffic | 2 |
| Baseline 5/10/15/30 | 3 |
| Weather impact separate | 4 |
| Weather-adjusted combine | 5 |
| Confidence | 5 |
| Nowcast auto-invoked | 6 |
| Missing/stale/unavailable nowcast | 4, 5, 6 |
| POST /api/traffic/prediction | 6 |
| Map current vs predicted | 8, 9 |
| Independent horizons | 7, 8 |
| Segment explainability popup | 7, 9 |
| Tests listed in spec | 1â€“6, 10 |
| Ready for live provider / ML | Protocol + TrafficPredictionModel |
| No Stage 1â€“5 rewrite | All additive |
| No Stage 7 routing | Out of scope |

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-25-stage6-traffic-prediction.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** â€” fresh subagent per task, review between tasks
2. **Inline Execution** â€” execute tasks in this session with executing-plans checkpoints

Which approach?
