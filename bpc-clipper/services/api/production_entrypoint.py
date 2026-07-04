"""Production ASGI entrypoint for Titan Clipper.

Use this module in hosting environments instead of importing ``main:app`` directly.
It applies a strict, configurable CORS policy without changing local-development defaults.
"""

import os

from fastapi.middleware.cors import CORSMiddleware

from main import app


def allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    if not raw:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


origins = allowed_origins()
if "*" in origins:
    raise RuntimeError("ALLOWED_ORIGINS must name explicit web origins in production.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Workspace-Key"],
)
