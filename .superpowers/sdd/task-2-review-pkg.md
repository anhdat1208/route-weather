# Review package Task 2
BASE: d9656e52b5855f2ea106b0930f02a086874e479c
HEAD: 31a32a8045d47534e3127983929d7d778d877b5b

## Commits
31a32a8 feat(nowcast): add baseline extrapolation model

## Stat
 backend/app/engine/nowcasting_models.py   | 207 +++++++++++++++++++++++++++++
 backend/tests/test_nowcasting_baseline.py | 214 ++++++++++++++++++++++++++++++
 2 files changed, 421 insertions(+)

## Diff
diff --git a/backend/app/engine/nowcasting_models.py b/backend/app/engine/nowcasting_models.py
new file mode 100644
index 0000000..ca815f8
--- /dev/null
+++ b/backend/app/engine/nowcasting_models.py
@@ -0,0 +1,207 @@
+from __future__ import annotations
+
+from datetime import datetime
+from typing import Protocol, Sequence
+
+from app.config import settings
+from app.engine.geo_math import destination_point
+from app.schemas.common import LatLng
+from app.schemas.nowcasting import PredictedCellMotion, PredictedRainCell
+from app.schemas.rain_cell import CellBoundsOut, TrackedRainCellOut
+
+_ELIGIBLE_STATES = frozenset({"TRACKING", "NEW"})
+
+
+class NowcastingModel(Protocol):
+    def predict(
+        self,
+        cells: Sequence[TrackedRainCellOut],
+        *,
+        frames_used: int,
+        radar_age_seconds: int | None,
+        horizons: list[int],
+    ) -> list[PredictedRainCell]: ...
+
+
+def _parse_timestamp(value: str) -> datetime | None:
+    try:
+        return datetime.fromisoformat(value.replace("Z", "+00:00"))
+    except ValueError:
+        return None
+
+
+def _intensity_samples(cell: TrackedRainCellOut) -> list[tuple[float, float]]:
+    dated: list[tuple[datetime, float]] = []
+    for item in (*cell.history, cell.current):
+        if item.intensity is None or item.intensity.mean is None:
+            continue
+        parsed = _parse_timestamp(item.timestamp)
+        if parsed is None:
+            continue
+        dated.append((parsed, item.intensity.mean))
+    if not dated:
+        return []
+    dated.sort(key=lambda pair: pair[0])
+    origin = dated[0][0]
+    return [((ts - origin).total_seconds() / 60.0, mean) for ts, mean in dated]
+
+
+def _linear_slope(samples: list[tuple[float, float]]) -> float:
+    n = len(samples)
+    xs = [x for x, _ in samples]
+    ys = [y for _, y in samples]
+    mean_x = sum(xs) / n
+    mean_y = sum(ys) / n
+    denom = sum((x - mean_x) ** 2 for x in xs)
+    if denom == 0:
+        return 0.0
+    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / denom
+
+
+def _extrapolate_intensity(cell: TrackedRainCellOut, forecast_minutes: int) -> float | None:
+    current_mean = cell.current.intensity.mean if cell.current.intensity is not None else None
+    samples = _intensity_samples(cell)
+    if len(samples) >= 2:
+        base = current_mean if current_mean is not None else samples[-1][1]
+        predicted = base + _linear_slope(samples) * forecast_minutes
+    else:
+        predicted = current_mean
+    if predicted is None:
+        return None
+    return max(0.0, min(float(settings.nowcast_intensity_max), predicted))
+
+
+def _confidence(
+    cell: TrackedRainCellOut,
+    *,
+    forecast_minutes: int,
+    frames_used: int,
+    radar_age_seconds: int | None,
+    missing_motion_vector: bool,
+) -> float:
+    motion = cell.motion
+    base = 0.4
+    if motion is not None and motion.confidence is not None:
+        base = motion.confidence
+    value = base * max(0.25, 1 - forecast_minutes / 90)
+    if frames_used < settings.nowcast_min_frames_for_full_confidence:
+        value *= 0.7
+    if len(cell.history) < 2:
+        value *= 0.75
+    if missing_motion_vector:
+        value *= 0.5
+    if radar_age_seconds and radar_age_seconds > settings.radar_stale_after_seconds:
+        value *= 0.6
+    if missing_motion_vector:
+        value = min(value, 0.35)
+    return max(0.0, min(1.0, value))
+
+
+def _copy_latlng(point: LatLng) -> LatLng:
+    return LatLng(lat=point.lat, lng=point.lng)
+
+
+def _copy_bounds(bounds: CellBoundsOut | None) -> CellBoundsOut | None:
+    if bounds is None:
+        return None
+    return CellBoundsOut(north=bounds.north, south=bounds.south, east=bounds.east, west=bounds.west)
+
+
+def _translate_bounds(bounds: CellBoundsOut, dlat: float, dlng: float) -> CellBoundsOut:
+    return CellBoundsOut(
+        north=bounds.north + dlat,
+        south=bounds.south + dlat,
+        east=bounds.east + dlng,
+        west=bounds.west + dlng,
+    )
+
+
+class BaselineExtrapolationModel:
+    @property
+    def name(self) -> str:
+        return settings.nowcast_model_name
+
+    @property
+    def version(self) -> str:
+        return settings.nowcast_model_version
+
+    def predict(
+        self,
+        cells: Sequence[TrackedRainCellOut],
+        *,
+        frames_used: int,
+        radar_age_seconds: int | None,
+        horizons: list[int],
+    ) -> list[PredictedRainCell]:
+        predictions: list[PredictedRainCell] = []
+        for cell in cells:
+            if cell.state not in _ELIGIBLE_STATES:
+                continue
+            predictions.extend(
+                self._predict_cell(
+                    cell,
+                    frames_used=frames_used,
+                    radar_age_seconds=radar_age_seconds,
+                    horizons=horizons,
+                )
+            )
+        return predictions
+
+    def _predict_cell(
+        self,
+        cell: TrackedRainCellOut,
+        *,
+        frames_used: int,
+        radar_age_seconds: int | None,
+        horizons: list[int],
+    ) -> list[PredictedRainCell]:
+        motion = cell.motion
+        speed = motion.speed_kmh if motion is not None else None
+        bearing = motion.bearing_degrees if motion is not None else None
+        missing_motion_vector = speed is None or bearing is None
+        origin = cell.current.centroid
+        origin_bounds = cell.current.bounds
+
+        out: list[PredictedRainCell] = []
+        for forecast_minutes in horizons:
+            if missing_motion_vector:
+                centroid = _copy_latlng(origin)
+                bounds = _copy_bounds(origin_bounds)
+            else:
+                distance_km = float(speed) * (forecast_minutes / 60.0)
+                centroid = destination_point(origin, distance_km, float(bearing))
+                if origin_bounds is None:
+                    bounds = None
+                else:
+                    bounds = _translate_bounds(
+                        origin_bounds,
+                        centroid.lat - origin.lat,
+                        centroid.lng - origin.lng,
+                    )
+
+            intensity = _extrapolate_intensity(cell, forecast_minutes)
+            probability = None
+            if intensity is not None:
+                probability = max(0.0, min(1.0, intensity / settings.nowcast_intensity_max))
+
+            out.append(
+                PredictedRainCell(
+                    cell_id=cell.id,
+                    forecast_minutes=forecast_minutes,
+                    kind="predicted",
+                    centroid=centroid,
+                    bounds=bounds,
+                    rain_probability=probability,
+                    rain_intensity=intensity,
+                    confidence=_confidence(
+                        cell,
+                        forecast_minutes=forecast_minutes,
+                        frames_used=frames_used,
+                        radar_age_seconds=radar_age_seconds,
+                        missing_motion_vector=missing_motion_vector,
+                    ),
+                    motion=PredictedCellMotion(speed_kmh=speed, bearing_degrees=bearing),
+                    source="rain_cell_track+baseline",
+                )
+            )
+        return out
diff --git a/backend/tests/test_nowcasting_baseline.py b/backend/tests/test_nowcasting_baseline.py
new file mode 100644
index 0000000..6ea4d27
--- /dev/null
+++ b/backend/tests/test_nowcasting_baseline.py
@@ -0,0 +1,214 @@
+from __future__ import annotations
+
+from datetime import datetime, timedelta, timezone
+
+import pytest
+
+from app.config import settings
+from app.engine.geo_math import haversine_distance_m
+from app.engine.nowcasting_models import BaselineExtrapolationModel
+from app.schemas.common import LatLng
+from app.schemas.rain_cell import (
+    CellBoundsOut,
+    CellIntensityOut,
+    CellMotionOut,
+    RainCellOut,
+    TrackedRainCellOut,
+)
+
+T0 = datetime(2026, 8, 24, 3, 35, tzinfo=timezone.utc)
+ORIGIN = LatLng(lat=10.0, lng=106.0)
+BOUNDS = CellBoundsOut(north=10.05, south=9.95, east=106.05, west=105.95)
+HORIZONS = [5, 10, 15, 30, 60]
+
+
+def _ts(minutes_before: int) -> str:
+    return (T0 - timedelta(minutes=minutes_before)).isoformat()
+
+
+def _cell_out(
+    *,
+    cell_id: str = "c1",
+    minutes_before: int = 0,
+    centroid: LatLng | None = None,
+    mean: float | None = 60.0,
+    bounds: CellBoundsOut | None = BOUNDS,
+) -> RainCellOut:
+    intensity = None if mean is None else CellIntensityOut(min=mean - 10, max=mean + 10, mean=mean)
+    return RainCellOut(
+        id=f"{cell_id}-t{minutes_before}",
+        timestamp=_ts(minutes_before),
+        centroid=centroid or ORIGIN,
+        area_km2=12.0,
+        intensity=intensity,
+        bounds=bounds,
+    )
+
+
+def _tracked(
+    *,
+    cell_id: str = "c1",
+    state: str = "TRACKING",
+    speed_kmh: float | None = 60.0,
+    bearing_degrees: float | None = 90.0,
+    motion_confidence: float | None = 1.0,
+    history_means: list[tuple[int, float]] | None = None,
+    current_mean: float | None = 60.0,
+    include_motion: bool = True,
+) -> TrackedRainCellOut:
+    history_means = history_means if history_means is not None else [(20, 40.0), (10, 50.0)]
+    history = [
+        _cell_out(cell_id=cell_id, minutes_before=mins, mean=mean) for mins, mean in history_means
+    ]
+    motion = None
+    if include_motion:
+        motion = CellMotionOut(
+            speed_kmh=speed_kmh,
+            bearing_degrees=bearing_degrees,
+            from_point=ORIGIN,
+            to_point=ORIGIN,
+            confidence=motion_confidence,
+        )
+    return TrackedRainCellOut(
+        id=cell_id,
+        state=state,  # type: ignore[arg-type]
+        current=_cell_out(cell_id=cell_id, minutes_before=0, mean=current_mean),
+        history=history,
+        motion=motion,
+        missed_frames=0,
+    )
+
+
+def test_horizons_emit_five_predictions_per_cell():
+    model = BaselineExtrapolationModel()
+    cell = _tracked()
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    assert sorted({p.forecast_minutes for p in preds}) == [5, 10, 15, 30, 60]
+    assert all(p.kind == "predicted" for p in preds)
+    assert all(p.cell_id == "c1" for p in preds)
+    assert all(p.source == "rain_cell_track+baseline" for p in preds)
+    assert model.name == settings.nowcast_model_name
+    assert model.version == settings.nowcast_model_version
+
+
+def test_projects_centroid_with_speed_and_bearing():
+    model = BaselineExtrapolationModel()
+    cell = _tracked(speed_kmh=60.0, bearing_degrees=90.0)
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    plus_5 = next(p for p in preds if p.forecast_minutes == 5)
+    dist_m = haversine_distance_m(ORIGIN, plus_5.centroid)
+    assert abs(dist_m - 5000.0) < 500.0
+    assert plus_5.centroid.lng > ORIGIN.lng
+    assert abs(plus_5.centroid.lat - ORIGIN.lat) < 0.05
+    assert plus_5.bounds is not None
+    assert plus_5.bounds.east > BOUNDS.east
+    assert plus_5.bounds.west > BOUNDS.west
+    assert plus_5.motion is not None
+    assert plus_5.motion.speed_kmh == 60.0
+    assert plus_5.motion.bearing_degrees == 90.0
+
+
+def test_missing_velocity_holds_position_low_confidence():
+    model = BaselineExtrapolationModel()
+    cell = _tracked(speed_kmh=None, bearing_degrees=90.0, motion_confidence=1.0)
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    assert len(preds) == 5
+    for p in preds:
+        assert p.centroid.lat == ORIGIN.lat
+        assert p.centroid.lng == ORIGIN.lng
+        assert p.bounds is not None
+        assert p.bounds.north == BOUNDS.north
+        assert p.bounds.south == BOUNDS.south
+        assert p.bounds.east == BOUNDS.east
+        assert p.bounds.west == BOUNDS.west
+        assert p.confidence <= 0.35
+
+
+def test_missing_direction_holds_position_low_confidence():
+    model = BaselineExtrapolationModel()
+    cell = _tracked(speed_kmh=60.0, bearing_degrees=None, motion_confidence=1.0)
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    assert len(preds) == 5
+    for p in preds:
+        assert p.centroid.lat == ORIGIN.lat
+        assert p.centroid.lng == ORIGIN.lng
+        assert p.confidence <= 0.35
+
+
+def test_intensity_extrapolates_from_history():
+    model = BaselineExtrapolationModel()
+    cell = _tracked(history_means=[(20, 40.0), (10, 50.0)], current_mean=60.0)
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    plus_5 = next(p for p in preds if p.forecast_minutes == 5)
+    plus_60 = next(p for p in preds if p.forecast_minutes == 60)
+    assert plus_5.rain_intensity == pytest.approx(65.0)
+    assert plus_60.rain_intensity == pytest.approx(120.0)
+    assert plus_5.rain_probability == pytest.approx(65.0 / settings.nowcast_intensity_max)
+    assert plus_60.rain_probability == pytest.approx(120.0 / settings.nowcast_intensity_max)
+
+
+def test_intensity_fallback_without_history():
+    model = BaselineExtrapolationModel()
+    cell = _tracked(history_means=[], current_mean=80.0)
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    assert len(preds) == 5
+    for p in preds:
+        assert p.rain_intensity == pytest.approx(80.0)
+        assert p.rain_probability == pytest.approx(80.0 / settings.nowcast_intensity_max)
+
+
+def test_confidence_decreases_with_horizon():
+    model = BaselineExtrapolationModel()
+    cell = _tracked()
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    confs = [p.confidence for p in preds if p.cell_id == "c1"]
+    assert confs == sorted(confs, reverse=True)
+    assert len(confs) == 5
+
+
+def test_stale_radar_reduces_confidence():
+    model = BaselineExtrapolationModel()
+    cell = _tracked()
+    fresh = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    stale = model.predict(
+        [cell],
+        frames_used=4,
+        radar_age_seconds=settings.radar_stale_after_seconds + 1,
+        horizons=HORIZONS,
+    )
+    for f, s in zip(fresh, stale, strict=True):
+        assert s.confidence == pytest.approx(f.confidence * 0.6)
+        assert s.confidence < f.confidence
+
+
+def test_short_history_reduces_confidence():
+    model = BaselineExtrapolationModel()
+    long_hist = _tracked(cell_id="c1", history_means=[(20, 40.0), (10, 50.0)])
+    short_hist = _tracked(cell_id="c2", history_means=[])
+    long_preds = model.predict([long_hist], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    short_preds = model.predict([short_hist], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    for long_p, short_p in zip(long_preds, short_preds, strict=True):
+        assert short_p.confidence == pytest.approx(long_p.confidence * 0.75)
+        assert short_p.confidence < long_p.confidence
+
+
+def test_lost_cells_omitted():
+    model = BaselineExtrapolationModel()
+    tracking = _tracked(cell_id="c1", state="TRACKING")
+    lost = _tracked(cell_id="lost", state="LOST")
+    expired = _tracked(cell_id="expired", state="EXPIRED")
+    new = _tracked(cell_id="new", state="NEW")
+    preds = model.predict(
+        [tracking, lost, expired, new],
+        frames_used=4,
+        radar_age_seconds=120,
+        horizons=HORIZONS,
+    )
+    ids = {p.cell_id for p in preds}
+    assert ids == {"c1", "new"}
+    assert len(preds) == 10
+
+
+def test_no_cells_returns_empty():
+    model = BaselineExtrapolationModel()
+    assert model.predict([], frames_used=3, radar_age_seconds=60, horizons=HORIZONS) == []
