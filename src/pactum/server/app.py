"""
FastAPI Server Factory for Pactum Barter Kernel.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from pactum.core.config import PactumConfig
from pactum.engine.kernel import PactumKernel
from pactum.server.routes import create_api_router


def create_app(kernel: Optional[PactumKernel] = None, config: Optional[PactumConfig] = None) -> FastAPI:
    app_config = config or PactumConfig()
    app_kernel = kernel or PactumKernel(service_id="pactum-local-node", config=app_config)

    app = FastAPI(
        title="Pactum Barter Kernel",
        description="Coasian Micro-Resource Bartering & Ephemeral Capability Exchange Kernel",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.kernel = app_kernel

    api_router = create_api_router(app_kernel)
    app.include_router(api_router)

    static_dir = Path(__file__).parent.parent / "web" / "static"
    index_file = static_dir / "index.html"

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def serve_dashboard():
        if index_file.exists():
            return FileResponse(str(index_file))
        return HTMLResponse("<h1>Pactum Barter Kernel Running</h1>")

    return app
