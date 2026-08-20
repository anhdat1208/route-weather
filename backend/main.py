"""ASGI entrypoint for Vercel and local uvicorn.

Vercel Root Directory must be `backend`.
"""

from app.main import app

__all__ = ["app"]
