# Review package Task 1
BASE: f6e16fa26208478a499998308556cec47666b77a
HEAD: d9656e52b5855f2ea106b0930f02a086874e479c

## Commits


## Stat
 backend/app/config.py                      |  6 ----
 backend/app/engine/geo_math.py             | 19 ------------
 backend/app/schemas/nowcasting.py          | 50 ------------------------------
 backend/tests/test_geo_math_destination.py | 21 -------------
 4 files changed, 96 deletions(-)

## Diff
diff --cc backend/app/config.py
index 9d575a9,9d575a9..3c587bc
--- a/backend/app/config.py
+++ b/backend/app/config.py
@@@ -78,26 -78,26 +78,20 @@@ class Settings(BaseSettings)
      route_weather_max_points: int = 20
      route_weather_min_points: int = 5
      route_weather_sample_interval_km: float = 10.0
  
      # Risk thresholds
      risk_threshold_low: int = 20
      risk_threshold_moderate: int = 40
      risk_threshold_high: int = 60
      risk_threshold_very_high: int = 80
  
--    nowcast_model_name: str = "baseline"
--    nowcast_model_version: str = "0.1"
--    nowcast_horizons_minutes: list[int] = [5, 10, 15, 30, 60]
--    nowcast_intensity_max: float = 255.0
--    nowcast_min_frames_for_full_confidence: int = 3
--
      # Server
      backend_host: str = "0.0.0.0"
      backend_port: int = 8000
      cors_origins: str = "http://localhost:3000,https://route-weather-tracking.vercel.app"
  
      @property
      def cors_origin_list(self) -> list[str]:
          return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
  
  
diff --cc backend/app/engine/geo_math.py
index 6797381,6797381..ca631a4
--- a/backend/app/engine/geo_math.py
+++ b/backend/app/engine/geo_math.py
@@@ -1,39 -1,39 +1,20 @@@
  from __future__ import annotations
  
  import math
  
  from app.schemas.common import LatLng
  
  
  EARTH_RADIUS_M = 6371000.0
  
  
--def destination_point(origin: LatLng, distance_km: float, bearing_degrees: float) -> LatLng:
--    """Move from origin along initial bearing by distance_km (spherical Earth)."""
--    if distance_km <= 0:
--        return LatLng(lat=origin.lat, lng=origin.lng)
--    lat1 = math.radians(origin.lat)
--    lng1 = math.radians(origin.lng)
--    brng = math.radians(bearing_degrees)
--    angular = (distance_km * 1000.0) / EARTH_RADIUS_M
--    lat2 = math.asin(
--        math.sin(lat1) * math.cos(angular)
--        + math.cos(lat1) * math.sin(angular) * math.cos(brng)
--    )
--    lng2 = lng1 + math.atan2(
--        math.sin(brng) * math.sin(angular) * math.cos(lat1),
--        math.cos(angular) - math.sin(lat1) * math.sin(lat2),
--    )
--    return LatLng(lat=math.degrees(lat2), lng=((math.degrees(lng2) + 540) % 360) - 180)
--
--
  def haversine_distance_m(a: LatLng, b: LatLng) -> float:
      """Distance in meters between two WGS84 points."""
  
      lat1 = math.radians(a.lat)
      lat2 = math.radians(b.lat)
      dlat = lat2 - lat1
      dlng = math.radians(b.lng - a.lng)
  
      h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
      return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))
diff --cc backend/app/schemas/nowcasting.py
index 29be220,29be220..0000000
deleted file mode 100644,100644
--- a/backend/app/schemas/nowcasting.py
+++ /dev/null
@@@ -1,50 -1,50 +1,0 @@@
--from __future__ import annotations
--
--from datetime import datetime
--from typing import Literal
--
--from pydantic import BaseModel, Field
--
--from app.schemas.common import LatLng
--from app.schemas.rain_cell import CellBoundsOut
--
--NowcastStatus = Literal["ok", "partial", "unavailable"]
--
--
--class NowcastPredictRequest(BaseModel):
--    geometry: list[LatLng] = Field(..., min_length=2)
--    buffer_km: float | None = Field(default=None, ge=1, le=300)
--
--
--class NowcastModelInfo(BaseModel):
--    name: str
--    version: str
--
--
--class PredictedCellMotion(BaseModel):
--    speed_kmh: float | None = None
--    bearing_degrees: float | None = None
--
--
--class PredictedRainCell(BaseModel):
--    cell_id: str
--    forecast_minutes: int
--    kind: Literal["predicted"] = "predicted"
--    centroid: LatLng
--    bounds: CellBoundsOut | None = None
--    rain_probability: float | None = Field(default=None, ge=0, le=1)
--    rain_intensity: float | None = None
--    confidence: float = Field(..., ge=0, le=1)
--    motion: PredictedCellMotion | None = None
--    source: str = "rain_cell_track+baseline"
--
--
--class NowcastPredictionResponse(BaseModel):
--    generated_at: datetime
--    status: NowcastStatus
--    model: NowcastModelInfo
--    frames_used: int
--    radar_age_seconds: int | None = None
--    horizons: list[int]
--    predictions: list[PredictedRainCell]
--    message: str | None = None
diff --cc backend/tests/test_geo_math_destination.py
index 8075d0e,8075d0e..0000000
deleted file mode 100644,100644
--- a/backend/tests/test_geo_math_destination.py
+++ /dev/null
@@@ -1,21 -1,21 +1,0 @@@
--from __future__ import annotations
--
--from app.engine.geo_math import destination_point, haversine_distance_m
--from app.schemas.common import LatLng
--
--
--def test_destination_point_north_1km():
--    origin = LatLng(lat=10.0, lng=106.0)
--    dest = destination_point(origin, distance_km=1.0, bearing_degrees=0.0)
--    dist_m = haversine_distance_m(origin, dest)
--    assert abs(dist_m - 1000.0) < 15.0
--    assert dest.lat > origin.lat
--    assert abs(dest.lng - origin.lng) < 1e-4
--
--
--def test_destination_point_east_and_zero():
--    origin = LatLng(lat=10.0, lng=106.0)
--    east = destination_point(origin, distance_km=2.0, bearing_degrees=90.0)
--    assert east.lng > origin.lng
--    same = destination_point(origin, distance_km=0.0, bearing_degrees=123.0)
--    assert same.lat == origin.lat and same.lng == origin.lng
