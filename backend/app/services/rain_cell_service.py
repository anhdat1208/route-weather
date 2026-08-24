from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.engine.geo_math import bounds_from_geometry
from app.engine.radar_models import RadarBounds, RainCellDetection, TrackedRainCell
from app.engine.radar_mosaic import build_radar_frame_from_tiles
from app.engine.rain_cell_detect import detect_cells_in_frame
from app.engine.rain_cell_track import track_rain_cells
from app.providers.errors import ProviderRequestError
from app.providers.rainviewer import RainViewerProvider
from app.schemas.common import LatLng
from app.schemas.rain_cell import (
    CellBoundsOut,
    CellIntensityOut,
    CellMotionOut,
    RainCellOut,
    RainCellTrackResponse,
    TrackedRainCellOut,
)

logger = logging.getLogger(__name__)


class RainCellService:
    def __init__(self, provider: RainViewerProvider | None = None) -> None:
        self._provider = provider or RainViewerProvider()

    async def track_for_route(
        self,
        geometry: list[LatLng],
        *,
        buffer_km: float | None = None,
    ) -> RainCellTrackResponse:
        buffer = buffer_km if buffer_km is not None else settings.rain_cell_buffer_km
        north, south, east, west = bounds_from_geometry(geometry, buffer)
        bounds = RadarBounds(north=north, south=south, east=east, west=west)

        try:
            provider_frames = await self._provider.fetch_past_frames(settings.rain_cell_frame_count)
        except ProviderRequestError as exc:
            logger.warning("Rain-cell track: radar unavailable: %s", exc)
            return RainCellTrackResponse(
                status="unavailable",
                frames_used=0,
                cells=[],
                message="Dữ liệu radar tạm thời không khả dụng.",
            )

        frame_detections: list[tuple] = []
        frames_built = 0

        async with httpx.AsyncClient(timeout=25.0) as client:
            for pf in provider_frames:
                radar_frame = await build_radar_frame_from_tiles(
                    provider_frame=pf,
                    bounds=bounds,
                    zoom=settings.rain_cell_tile_zoom,
                    client=client,
                )
                if radar_frame is None:
                    continue
                frames_built += 1
                detections = detect_cells_in_frame(
                    radar_frame,
                    min_intensity=settings.rain_cell_min_intensity,
                    min_area_pixels=settings.rain_cell_min_area_pixels,
                    max_area_pixels=settings.rain_cell_max_area_pixels,
                )
                frame_detections.append((radar_frame, detections))

        if frames_built == 0:
            return RainCellTrackResponse(
                status="unavailable",
                frames_used=0,
                cells=[],
                message="Không có dữ liệu radar trong hành lang lộ trình.",
            )

        tracked = track_rain_cells(
            frame_detections,
            max_match_distance_km=settings.rain_cell_max_match_distance_km,
            history_frames=settings.rain_cell_history_frames,
            max_missed_frames=settings.rain_cell_max_missed_frames,
            route_geometry=geometry,
        )

        status = "ok" if frames_built >= settings.rain_cell_frame_count else "partial"
        return RainCellTrackResponse(
            status=status,
            frames_used=frames_built,
            cells=[_to_api_cell(t) for t in tracked],
            message=None if status == "ok" else "Một số khung radar không khả dụng trong hành lang lộ trình.",
        )


def _to_api_cell(track: TrackedRainCell) -> TrackedRainCellOut:
    return TrackedRainCellOut(
        id=track.id,
        state=track.state,  # type: ignore[arg-type]
        current=_detection_to_out(track.current),
        history=[_detection_to_out(h) for h in track.history],
        motion=_motion_to_out(track.motion),
        distance_to_route_km=track.distance_to_route_km,
        missed_frames=track.missed_frames,
    )


def _detection_to_out(det: RainCellDetection) -> RainCellOut:
    intensity = None
    if det.intensity.mean is not None:
        intensity = CellIntensityOut(
            min=det.intensity.min,
            max=det.intensity.max,
            mean=round(det.intensity.mean, 1) if det.intensity.mean is not None else None,
        )
    bounds = CellBoundsOut(
        north=det.bounds.north,
        south=det.bounds.south,
        east=det.bounds.east,
        west=det.bounds.west,
    )
    return RainCellOut(
        id=det.frame_id,
        timestamp=det.timestamp.isoformat(),
        centroid=det.centroid,
        area_km2=det.area_km2,
        intensity=intensity,
        bounds=bounds,
    )


def _motion_to_out(motion) -> CellMotionOut | None:
    if motion is None:
        return None
    return CellMotionOut(
        speed_kmh=motion.speed_kmh,
        bearing_degrees=motion.bearing_degrees,
        from_point=motion.from_point,
        to_point=motion.to_point,
        confidence=motion.confidence,
    )


_rain_cell_service: RainCellService | None = None


def get_rain_cell_service() -> RainCellService:
    global _rain_cell_service
    if _rain_cell_service is None:
        _rain_cell_service = RainCellService()
    return _rain_cell_service
