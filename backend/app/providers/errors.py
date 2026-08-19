from __future__ import annotations


class ProviderNotConfiguredError(RuntimeError):
    pass


class ProviderRequestError(RuntimeError):
    pass


class WeatherNotAvailableError(RuntimeError):
    pass

