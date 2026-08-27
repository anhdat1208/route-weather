from __future__ import annotations

from datetime import datetime, timezone

from app.engine.traffic_models import BaselineTrafficModel
from app.providers.synthetic_traffic import SyntheticTrafficProvider
from app.schemas.common import LatLng

GEOM = [LatLng(lat=10.70, lng=106.65), LatLng(lat=10.85, lng=106.80)]


def test_baseline_emits_all_horizons():
    at = datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)
    segs = SyntheticTrafficProvider().current_for_route(GEOM, at=at)
    model = BaselineTrafficModel()
    out = model.predict_base(segs, at=at, horizons=[5, 10, 15, 30])
    keys = {(sid, h) for sid, h, _ in out}
    assert len(segs) * 4 == len(out)
    assert (segs[0].id, 5) in keys and (segs[0].id, 30) in keys
    assert model.name == "baseline" and model.version == "0.1"


def test_baseline_speed_within_clamp():
    at = datetime(2026, 8, 25, 2, 0, tzinfo=timezone.utc)
    segs = SyntheticTrafficProvider().current_for_route(GEOM, at=at)
    pair = BaselineTrafficModel().predict_base(segs, at=at, horizons=[15])[0][2]
    free = segs[0].traffic.free_flow_speed_kmh
    assert pair.speed_kmh is not None
    assert 0.20 * free - 1e-6 <= pair.speed_kmh <= 1.05 * free + 1e-6
