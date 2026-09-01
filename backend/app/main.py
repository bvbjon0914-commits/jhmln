"""
FastAPI Hauptanwendung für Authority Matching System

Dieses System ermittelt automatisch zuständige Behörden für Gebäudeadressen
und generiert Anschreiben als Word-Dokumente.
"""

import logging
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Datenbank
from app.database import init_db

# API-Routen
from app.api import buildings, authorities, request_types, matching, documents, requests_api, imports, geo, jurisdictions, auth
from app.api.auth import require_login

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== Lifespan Events ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/Shutdown Events
    """
    # Startup
    logger.info("🚀 Starting Authority Matching System...")
    init_db()
    logger.info("✓ Database initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Authority Matching System...")


# ========== FastAPI App Initialisierung ==========

app = FastAPI(
    title="Authority Matching System",
    description="Automatische Ermittlung zuständiger Behörden für Gebäudeadressen",
    version="1.0.0",
    lifespan=lifespan,
)

# ========== CORS Middleware ==========

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠ In Production: Spezifische Origins!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

# ========== Health Check ==========

@app.get("/health", tags=["System"])
async def health_check():
    """Health Check Endpoint"""
    return {
        "status": "ok",
        "service": "Authority Matching System",
        "version": "1.0.0",
    }


# ========== Frontend (Production Build) ==========
# Wird nur bedient, wenn frontend/dist existiert (z.B. auf Render nach "npm run build").
# Lokal im Dev-Betrieb läuft das Frontend separat über Vite, daher bleibt dieser Block dort inaktiv.

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
SERVE_FRONTEND = FRONTEND_DIST.is_dir()

if SERVE_FRONTEND:
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")
else:
    @app.get("/", tags=["System"])
    async def root():
        """Root Endpoint mit API-Informationen (nur im reinen API-Dev-Betrieb ohne gebautes Frontend)."""
        return {
            "service": "Authority Matching System",
            "version": "1.0.0",
            "description": "Automatische Ermittlung zuständiger Behörden für Gebäudeadressen",
            "endpoints": {
                "buildings": "/api/buildings",
                "authorities": "/api/authorities",
                "request_types": "/api/request-types",
                "matching": "/api/matching",
                "documents": "/api/documents",
                "requests": "/api/requests",
                "docs": "/docs",
                "health": "/health",
            }
        }


# ========== API Routes ==========

protected = [Depends(require_login)]

app.include_router(auth.router, prefix="/api")  # öffentlich (Login selbst darf nicht gesperrt sein)
app.include_router(buildings.router, prefix="/api", dependencies=protected)
app.include_router(authorities.router, prefix="/api", dependencies=protected)
app.include_router(request_types.router, prefix="/api", dependencies=protected)
app.include_router(matching.router, prefix="/api", dependencies=protected)
app.include_router(documents.router, prefix="/api", dependencies=protected)
app.include_router(requests_api.router, prefix="/api", dependencies=protected)
app.include_router(imports.router, prefix="/api", dependencies=protected)
app.include_router(geo.router, prefix="/api", dependencies=protected)
app.include_router(jurisdictions.router, prefix="/api", dependencies=protected)

# SPA-Fallback: muss nach allen /api-Routen registriert werden, sonst würde
# er sie abfangen. Liefert index.html für jede Route, die kein API-Aufruf ist.
if SERVE_FRONTEND:
    @app.get("/{full_path:path}", tags=["System"])
    async def serve_frontend(full_path: str):
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
