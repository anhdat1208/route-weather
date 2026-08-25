# Review package Task 4
BASE: 0ec15b326b036f475d6bc4dcd884789f1e9d6baf
HEAD: 0f4bf317457579bd3415a4ec531f360fc5d37a97

## Commits
0f4bf31 feat(nowcast): expose POST /api/nowcasting/predict

## Stat
 backend/app/api/nowcasting.py              |  16 +++++
 backend/app/main.py                        |   8 +++
 backend/app/services/nowcasting_service.py |  28 ++++++++
 backend/tests/test_nowcasting_api.py       | 102 +++++++++++++++++++++++++++++
 4 files changed, 154 insertions(+)

## Diff
diff --git a/backend/app/api/nowcasting.py b/backend/app/api/nowcasting.py
new file mode 100644
index 0000000..511ce8f
--- /dev/null
+++ b/backend/app/api/nowcasting.py
@@ -0,0 +1,16 @@
+from __future__ import annotations
+
+from fastapi import APIRouter
+
+from app.schemas.nowcasting import NowcastPredictRequest, NowcastPredictionResponse
+from app.services.nowcasting_service import get_nowcasting_service
+
+router = APIRouter(tags=["nowcasting"])
+
+
+@router.post("/api/nowcasting/predict", response_model=NowcastPredictionResponse)
+async def nowcasting_predict(body: NowcastPredictRequest) -> NowcastPredictionResponse:
+    """Predict rain-cell motion along a route corridor (baseline extrapolation)."""
+    return await get_nowcasting_service().predict_for_route(
+        body.geometry, buffer_km=body.buffer_km
+    )
diff --git a/backend/app/main.py b/backend/app/main.py
index 4dcad8f..97dd478 100644
--- a/backend/app/main.py
+++ b/backend/app/main.py
@@ -35,20 +35,28 @@ try:
     app.include_router(weather_fusion_router)
     app.include_router(route_weather_router)
     try:
         from app.api.rain_cells import router as rain_cells_router
 
         app.include_router(rain_cells_router)
     except Exception:  # noqa: BLE001 - Stage 3 must not take down radar/route APIs
         import logging
 
         logging.getLogger(__name__).exception("Rain-cell router failed to load")
+    try:
+        from app.api.nowcasting import router as nowcasting_router
+
+        app.include_router(nowcasting_router)
+    except Exception:  # noqa: BLE001 - Stage 5 must not take down radar/route APIs
+        import logging
+
+        logging.getLogger(__name__).exception("Nowcasting router failed to load")
 except Exception:  # noqa: BLE001 - surface boot failures on Vercel
     import traceback
 
     _boot_error = traceback.format_exc()
     app.add_middleware(
         CORSMiddleware,
         allow_origins=["*"],
         allow_credentials=False,
         allow_methods=["*"],
         allow_headers=["*"],
diff --git a/backend/app/services/nowcasting_service.py b/backend/app/services/nowcasting_service.py
new file mode 100644
index 0000000..08b01f3
--- /dev/null
+++ b/backend/app/services/nowcasting_service.py
@@ -0,0 +1,28 @@
+from __future__ import annotations
+
+from app.engine.nowcasting_engine import run_nowcast
+from app.schemas.common import LatLng
+from app.schemas.nowcasting import NowcastPredictionResponse
+from app.services.rain_cell_service import get_rain_cell_service
+
+
+class NowcastingService:
+    async def predict_for_route(
+        self,
+        geometry: list[LatLng],
+        buffer_km: float | None = None,
+    ) -> NowcastPredictionResponse:
+        track = await get_rain_cell_service().track_for_route(
+            geometry, buffer_km=buffer_km
+        )
+        return run_nowcast(track)
+
+
+_nowcasting_service: NowcastingService | None = None
+
+
+def get_nowcasting_service() -> NowcastingService:
+    global _nowcasting_service
+    if _nowcasting_service is None:
+        _nowcasting_service = NowcastingService()
+    return _nowcasting_service
diff --git a/backend/tests/test_nowcasting_api.py b/backend/tests/test_nowcasting_api.py
new file mode 100644
index 0000000..cce440e
--- /dev/null
+++ b/backend/tests/test_nowcasting_api.py
@@ -0,0 +1,102 @@
+from __future__ import annotations
+
+from datetime import datetime, timezone
+from unittest.mock import AsyncMock, patch
+
+import pytest
+from httpx import ASGITransport, AsyncClient
+
+from app.main import app
+from app.schemas.common import LatLng
+from app.schemas.nowcasting import (
+    NowcastModelInfo,
+    NowcastPredictionResponse,
+    PredictedCellMotion,
+    PredictedRainCell,
+)
+from app.schemas.rain_cell import CellBoundsOut, RainCellTrackResponse
+from app.services.nowcasting_service import NowcastingService
+
+
+def _filled_prediction() -> NowcastPredictionResponse:
+    return NowcastPredictionResponse(
+        generated_at=datetime(2026, 8, 25, 4, 0, tzinfo=timezone.utc),
+        status="ok",
+        model=NowcastModelInfo(name="baseline", version="0.1"),
+        frames_used=4,
+        horizons=[5, 10, 15, 30, 60],
+        predictions=[
+            PredictedRainCell(
+                cell_id="cell-1",
+                forecast_minutes=5,
+                kind="predicted",
+                centroid=LatLng(lat=10.5, lng=106.5),
+                bounds=CellBoundsOut(
+                    north=10.55,
+                    south=10.45,
+                    east=106.55,
+                    west=106.45,
+                ),
+                rain_probability=0.5,
+                rain_intensity=60.0,
+                confidence=0.8,
+                motion=PredictedCellMotion(speed_kmh=60.0, bearing_degrees=90.0),
+            )
+        ],
+    )
+
+
+@pytest.mark.asyncio
+async def test_nowcasting_predict_endpoint_with_mock_service():
+    from app.services import nowcasting_service as ncs
+
+    mock_response = _filled_prediction()
+    service = AsyncMock()
+    service.predict_for_route = AsyncMock(return_value=mock_response)
+    previous = ncs._nowcasting_service
+    ncs._nowcasting_service = service
+
+    try:
+        transport = ASGITransport(app=app)
+        async with AsyncClient(transport=transport, base_url="http://test") as client:
+            resp = await client.post(
+                "/api/nowcasting/predict",
+                json={
+                    "geometry": [
+                        {"lat": 10.4, "lng": 106.4},
+                        {"lat": 10.6, "lng": 106.6},
+                    ],
+                },
+            )
+    finally:
+        ncs._nowcasting_service = previous
+
+    assert resp.status_code == 200
+    data = resp.json()
+    assert data["model"]["name"] == "baseline"
+    assert data["horizons"] == [5, 10, 15, 30, 60]
+    assert data["predictions"][0]["kind"] == "predicted"
+
+
+@pytest.mark.asyncio
+async def test_predict_for_route_calls_track_then_engine():
+    mock_track = RainCellTrackResponse(status="ok", frames_used=3, cells=[], message=None)
+    rain_svc = AsyncMock()
+    rain_svc.track_for_route = AsyncMock(return_value=mock_track)
+    geometry = [
+        LatLng(lat=10.4, lng=106.4),
+        LatLng(lat=10.6, lng=106.6),
+    ]
+
+    with patch(
+        "app.services.nowcasting_service.get_rain_cell_service",
+        return_value=rain_svc,
+    ):
+        result = await NowcastingService().predict_for_route(geometry, buffer_km=25.0)
+
+    rain_svc.track_for_route.assert_awaited_once_with(geometry, buffer_km=25.0)
+    assert result.status == "ok"
+    assert result.predictions == []
+    assert result.frames_used == 3
+    assert result.model.name == "baseline"
+    assert result.message == "Kh├┤ng c├│ ├┤ m╞░a ─æang theo d├╡i ─æß╗â dß╗▒ b├ío."
