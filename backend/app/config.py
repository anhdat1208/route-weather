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
        extra="ignore",
    )

    # GraphHopper
    graphhopper_api_key: str = ""
    graphhopper_base_url: str = "https://graphhopper.com/api/1"
    graphhopper_motorbike_profile: str = "bike"
    geocode_bbox: str = "102.1,8.2,109.5,23.4"

    # Open-Meteo
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"

    # Database (unused in MVP)
    database_url: str = ""

    # Cache TTL (seconds)
    cache_ttl_route: int = 86400
    cache_ttl_geocode: int = 604800
    cache_ttl_weather: int = 1800

    # Route Weather Engine
    route_weather_max_points: int = 20
    route_weather_min_points: int = 5

    # Risk thresholds
    risk_threshold_low: int = 20
    risk_threshold_moderate: int = 40
    risk_threshold_high: int = 60
    risk_threshold_very_high: int = 80

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000,https://route-weather-tracking.vercel.app"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
