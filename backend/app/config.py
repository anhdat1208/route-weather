from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_files() -> tuple[str, ...]:
    candidates = [
        Path(".env"),
        Path(__file__).resolve().parents[1] / ".env",  # backend/.env
    ]
    try:
        candidates.append(Path(__file__).resolve().parents[2] / ".env")  # monorepo root
    except IndexError:
        pass
    return tuple(str(p) for p in candidates if p.is_file())


class Settings(BaseSettings):
    # On Vercel, configure env vars in the dashboard. Locally, .env is optional.
    model_config = SettingsConfigDict(
        env_file=_env_files() or None,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # GraphHopper
    graphhopper_api_key: str = ""
    graphhopper_base_url: str = "https://graphhopper.com/api/1"
    graphhopper_motorbike_profile: str = "bike"
    geocode_bbox: str = "102.1,8.2,109.5,23.4"

    # Open-Meteo
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"

    # RainViewer radar (no key required)
    rainviewer_api_url: str = "https://api.rainviewer.com"
    radar_refresh_interval_seconds: int = 300
    radar_stale_after_seconds: int = 900
    satellite_refresh_interval_seconds: int = 600
    satellite_stale_after_seconds: int = 1800

    # Database (unused in MVP)
    database_url: str = ""

    # Cache TTL (seconds)
    cache_ttl_route: int = 86400
    cache_ttl_geocode: int = 604800
    cache_ttl_weather: int = 1800
    cache_ttl_radar: int = 120
    cache_ttl_satellite: int = 300

    # Rain-cell detection & tracking (implementation thresholds — not meteorological classes)
    rain_cell_min_intensity: float = 25.0
    rain_cell_min_area_pixels: int = 4
    rain_cell_max_area_pixels: int = 500_000
    rain_cell_max_match_distance_km: float = 80.0
    rain_cell_history_frames: int = 6
    rain_cell_max_missed_frames: int = 2
    rain_cell_frame_count: int = 4
    rain_cell_buffer_km: float = 50.0
    rain_cell_tile_zoom: int = 5

    # Satellite provider (NASA GIBS WMTS)
    satellite_provider_name: str = "nasa_gibs"
    gibs_wmts_capabilities_url: str = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml"
    gibs_satellite_layer: str = "Himawari_AHI_Band13_Clean_Infrared"
    gibs_tile_matrix_set: str = "GoogleMapsCompatible_Level6"
    gibs_tile_format: str = "png"
    gibs_tile_max_zoom: int = 6

    # Fusion thresholds
    forecast_stale_after_seconds: int = 3600
    fusion_alignment_max_seconds: int = 1200
    fusion_corridor_km: float = 25.0

    # Route Weather Engine
    route_weather_max_points: int = 20
    route_weather_min_points: int = 5
    route_weather_sample_interval_km: float = 10.0

    # Risk thresholds
    risk_threshold_low: int = 20
    risk_threshold_moderate: int = 40
    risk_threshold_high: int = 60
    risk_threshold_very_high: int = 80

    nowcast_model_name: str = "baseline"
    nowcast_model_version: str = "0.1"
    nowcast_horizons_minutes: list[int] = [5, 10, 15, 30, 60]
    nowcast_intensity_max: float = 255.0
    nowcast_min_frames_for_full_confidence: int = 3

    traffic_model_name: str = "baseline"
    traffic_model_version: str = "0.1"
    traffic_horizons_minutes: list[int] = [5, 10, 15, 30]
    traffic_sample_interval_km: float = 5.0
    traffic_sample_min_points: int = 3
    traffic_sample_max_points: int = 24
    traffic_free_flow_default_kmh: float = 40.0
    traffic_stale_after_seconds: int = 900
    traffic_rain_nearby_km: float = 8.0
    traffic_base_confidence: float = 0.75

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000,https://route-weather-tracking.vercel.app"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
