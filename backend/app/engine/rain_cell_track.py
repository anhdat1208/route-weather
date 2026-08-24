from __future__ import annotations

import uuid
from dataclasses import replace

from app.engine.geo_math import haversine_distance_m, initial_bearing_deg, min_distance_to_polyline_m
from app.engine.radar_models import (
    CellMotion,
    RainCellDetection,
    RadarFrame,
    TrackState,
    TrackedRainCell,
)
from app.schemas.common import LatLng


def track_rain_cells(
    frame_detections: list[tuple[RadarFrame, list[RainCellDetection]]],
    *,
    max_match_distance_km: float,
    history_frames: int,
    max_missed_frames: int,
    route_geometry: list[LatLng] | None = None,
) -> list[TrackedRainCell]:
    if not frame_detections:
        return []

    tracks: dict[str, TrackedRainCell] = {}

    for frame, detections in frame_detections:
        tracks = _associate_frame(
            tracks,
            frame,
            detections,
            max_match_distance_km=max_match_distance_km,
            history_frames=history_frames,
            max_missed_frames=max_missed_frames,
        )

    active = [t for t in tracks.values() if t.state != "EXPIRED"]
    if route_geometry:
        for track in active:
            dist_m = min_distance_to_polyline_m(track.current.centroid, route_geometry)
            track.distance_to_route_km = round(dist_m / 1000.0, 2)

    return active


def _associate_frame(
    tracks: dict[str, TrackedRainCell],
    frame: RadarFrame,
    detections: list[RainCellDetection],
    *,
    max_match_distance_km: float,
    history_frames: int,
    max_missed_frames: int,
) -> dict[str, TrackedRainCell]:
    prev_active = {tid: t for tid, t in tracks.items() if t.state in ("NEW", "TRACKING", "LOST")}

    pairs: list[tuple[float, str, RainCellDetection]] = []
    for tid, track in prev_active.items():
        for det in detections:
            score = _match_score(track.current, det, max_match_distance_km)
            if score is not None:
                pairs.append((score, tid, det))

    pairs.sort(key=lambda x: x[0], reverse=True)
    matched_tracks: set[str] = set()
    matched_dets: set[int] = set()
    assignments: dict[str, RainCellDetection] = {}

    for score, tid, det in pairs:
        det_key = id(det)
        if tid in matched_tracks or det_key in matched_dets:
            continue
        matched_tracks.add(tid)
        matched_dets.add(det_key)
        assignments[tid] = det

    updated: dict[str, TrackedRainCell] = {}

    for tid, track in tracks.items():
        if tid in assignments:
            det = assignments[tid]
            motion = _compute_motion(track.current, det, frame.timestamp)
            hist = list(track.history) + [track.current]
            hist = hist[-history_frames:]
            consecutive = track.consecutive_hits + 1
            conf = motion.confidence if motion else None
            if conf is not None and consecutive > 1:
                conf = min(1.0, conf + 0.05 * (consecutive - 1))
            if motion and conf is not None:
                motion = replace(motion, confidence=conf)
            updated[tid] = TrackedRainCell(
                id=tid,
                state="TRACKING",
                current=det,
                history=hist,
                motion=motion,
                missed_frames=0,
                consecutive_hits=consecutive,
            )
        elif track.state in ("NEW", "TRACKING", "LOST"):
            missed = track.missed_frames + 1
            state: TrackState = "LOST" if missed <= max_missed_frames else "EXPIRED"
            updated[tid] = TrackedRainCell(
                id=tid,
                state=state,
                current=track.current,
                history=list(track.history),
                motion=track.motion,
                missed_frames=missed,
                consecutive_hits=track.consecutive_hits,
            )
        else:
            updated[tid] = track

    for det in detections:
        if id(det) in matched_dets:
            continue
        tid = str(uuid.uuid4())
        updated[tid] = TrackedRainCell(
            id=tid,
            state="NEW",
            current=det,
            history=[],
            motion=None,
            missed_frames=0,
            consecutive_hits=1,
        )

    return updated


def _match_score(
    prev: RainCellDetection,
    curr: RainCellDetection,
    max_match_distance_km: float,
) -> float | None:
    dist_km = haversine_distance_m(prev.centroid, curr.centroid) / 1000.0
    if dist_km > max_match_distance_km:
        return None

    dist_score = 1.0 - (dist_km / max_match_distance_km)
    area_score = 0.0
    if prev.area_pixels > 0 and curr.area_pixels > 0:
        area_score = min(prev.area_pixels, curr.area_pixels) / max(prev.area_pixels, curr.area_pixels)

    int_score = 0.0
    pm = prev.intensity.mean
    cm = curr.intensity.mean
    if pm is not None and cm is not None and max(pm, cm) > 0:
        int_score = 1.0 - abs(pm - cm) / max(pm, cm)

    overlap = _bbox_overlap_ratio(prev, curr)
    return dist_score * 0.45 + area_score * 0.2 + int_score * 0.15 + overlap * 0.2


def _bbox_overlap_ratio(a: RainCellDetection, b: RainCellDetection) -> float:
    lat_overlap = max(0.0, min(a.bounds.north, b.bounds.north) - max(a.bounds.south, b.bounds.south))
    lng_overlap = max(0.0, min(a.bounds.east, b.bounds.east) - max(a.bounds.west, b.bounds.west))
    if lat_overlap <= 0 or lng_overlap <= 0:
        return 0.0
    inter = lat_overlap * lng_overlap
    area_a = (a.bounds.north - a.bounds.south) * (a.bounds.east - a.bounds.west)
    area_b = (b.bounds.north - b.bounds.south) * (b.bounds.east - b.bounds.west)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _compute_motion(
    prev: RainCellDetection,
    curr: RainCellDetection,
    curr_time,
) -> CellMotion | None:
    dt = (curr.timestamp - prev.timestamp).total_seconds()
    if dt <= 0:
        return None

    dist_m = haversine_distance_m(prev.centroid, curr.centroid)
    speed_kmh = (dist_m / dt) * 3.6
    bearing = initial_bearing_deg(prev.centroid, curr.centroid)
    dist_km = dist_m / 1000.0
    confidence = max(0.0, min(1.0, 1.0 - dist_km / 100.0))

    return CellMotion(
        speed_kmh=round(speed_kmh, 1),
        bearing_degrees=round(bearing, 1),
        from_point=prev.centroid,
        to_point=curr.centroid,
        confidence=round(confidence, 2),
    )
