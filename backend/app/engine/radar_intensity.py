from __future__ import annotations

from io import BytesIO

from PIL import Image

from app.engine.radar_models import INVALID_INTENSITY

# RainViewer Black & White scheme (color=0) encodes reflectivity as grayscale when alpha > 0.
# This is an implementation intensity index (0–255), not an authoritative dBZ classification.


def decode_rainviewer_intensity_png(data: bytes) -> list[float]:
    """Decode a 256×256 RainViewer tile to row-major intensity values."""

    img = Image.open(BytesIO(data)).convert("RGBA")
    w, h = img.size
    pixels = img.load()
    out: list[float] = []
    for row in range(h):
        for col in range(w):
            r, g, b, a = pixels[col, row]
            if a < 64:
                out.append(INVALID_INTENSITY)
            else:
                # Grayscale proxy from RGB; higher = stronger echo in B&W scheme.
                out.append(float(max(r, g, b)))
    return out
