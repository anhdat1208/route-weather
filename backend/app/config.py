from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # GraphHopper
    graphhopper_api_key: str = ""
    graphhopper_base_url: str = "https://graphhopper.com/api/1"
    # GraphHopper free plan often only supports `car`, `bike`, `foot` profiles.
    # Use `motorcycle` only if your plan includes it.
    graphhopper_motorbike_profile: str = "bike"

    # Open-Meteo
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"

    # Database
    database_url: str = "postgresql://routeweather:routeweather@localhost:5432/routeweather"

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
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
