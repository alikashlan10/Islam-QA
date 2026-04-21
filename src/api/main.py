from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import jobs  

def create_app() -> FastAPI:
    app = FastAPI(
        title="Islam QA API",
        description="Async ingestion + semantic search system",
        version="1.0.0",
    )

    # ── Middleware (optional but useful) ─────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten later in prod
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Health check  ──────────────────────────────────────────────
    @app.get("/health")
    def health():
        return {"status": "ok"}


    # ── Routers ─────────────────────────────────────────────────────
    app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])

    return app


app = create_app()