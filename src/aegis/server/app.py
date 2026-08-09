"""
FastAPI Server Application Factory for AegisKernel.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from aegis.core.config import AegisConfig
from aegis.core.kernel import AegisKernel
from aegis.server.routes import create_api_router


def create_app(kernel: Optional[AegisKernel] = None, config: Optional[AegisConfig] = None) -> FastAPI:
    """Creates configured FastAPI application instance."""
    app_config = config or AegisConfig()
    app_kernel = kernel or AegisKernel(app_config)

    app = FastAPI(
        title="AegisKernel",
        description="High-Assurance Runtime & Deterministic Verification Engine for Autonomous AI",
        version="0.1.0",
    )

    # Configure CORS for developer preview and cross-origin access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Attach kernel to app state
    app.state.kernel = app_kernel

    # Mount REST API
    api_router = create_api_router(app_kernel)
    app.include_router(api_router)

    # Serve static dashboard
    static_dir = Path(__file__).parent.parent / "web" / "static"
    index_file = static_dir / "index.html"

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def serve_dashboard():
        if index_file.exists():
            return FileResponse(str(index_file))
        return HTMLResponse("<h1>AegisKernel Engine Running</h1><p>Dashboard not found.</p>")

    return app
