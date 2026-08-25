from __future__ import annotations

from datetime import datetime, timezone

from app.config import settings
from app.engine.nowcasting_models import BaselineExtrapolationModel, NowcastingModel
from app.schemas.nowcasting import NowcastModelInfo, NowcastPredictionResponse, PredictedRainCell
from app.schemas.rain_cell import RainCellTrackResponse

_MSG_UNAVAILABLE = "Dữ liệu theo dõi ô mưa tạm thời không khả dụng."
_MSG_EMPTY = "Không có ô mưa đang theo dõi để dự báo."
_MSG_INCOMPLETE_MOTION = "Một số ô mưa thiếu vector chuyển động nên dự báo chưa đầy đủ."


def _missing_motion(pred: PredictedRainCell) -> bool:
    motion = pred.motion
    if motion is None:
        return True
    return motion.speed_kmh is None or motion.bearing_degrees is None


def _has_incomplete_motion(preds: list[PredictedRainCell]) -> bool:
    return any(pred.confidence < 0.35 and _missing_motion(pred) for pred in preds)


def run_nowcast(
    track: RainCellTrackResponse,
    *,
    model: NowcastingModel | None = None,
    generated_at: datetime | None = None,
    radar_age_seconds: int | None = None,
) -> NowcastPredictionResponse:
    active = model or BaselineExtrapolationModel()
    horizons = list(settings.nowcast_horizons_minutes)
    info = NowcastModelInfo(name=active.name, version=active.version)
    at = generated_at or datetime.now(timezone.utc)

    if track.status == "unavailable":
        return NowcastPredictionResponse(
            generated_at=at,
            status="unavailable",
            model=info,
            frames_used=track.frames_used,
            radar_age_seconds=radar_age_seconds,
            horizons=horizons,
            predictions=[],
            message=track.message or _MSG_UNAVAILABLE,
        )

    preds = active.predict(
        track.cells,
        frames_used=track.frames_used,
        radar_age_seconds=radar_age_seconds,
        horizons=horizons,
    )

    if track.status == "partial":
        status = "partial"
        message = track.message
    elif _has_incomplete_motion(preds):
        status = "partial"
        message = _MSG_INCOMPLETE_MOTION
    elif not preds:
        status = "ok"
        message = _MSG_EMPTY
    else:
        status = "ok"
        message = None

    return NowcastPredictionResponse(
        generated_at=at,
        status=status,
        model=info,
        frames_used=track.frames_used,
        radar_age_seconds=radar_age_seconds,
        horizons=horizons,
        predictions=preds,
        message=message,
    )
