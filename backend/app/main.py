"""
FastAPI Hauptanwendung für Authority Matching System

Dieses System ermittelt automatisch zuständige Behörden für Gebäudeadressen
und generiert Anschreiben als Word-Dokumente.
"""

import logging
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Datenbank
from app.config import ALLOWED_ORIGINS
from app.database import init_db

# API-Routen
from app.api import (
    buildings, authorities, request_types, matching, documents, requests_api,
    imports, geo, jurisdictions, auth, data_quality, cases, data_sources, mailbox_inbound,
    users,
)
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
    title="Civeloq API",
    description="Automatische Ermittlung zuständiger Behörden für Gebäudeadressen",
    version="1.0.0",
    lifespan=lifespan,
)

# ========== CORS Middleware ==========

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Request-Id"],
)

# ========== Request-ID + Fehlerbehandlung ==========
# Priorität 2 des Auditberichts, Befund "Fehlerbehandlung": es gab keinen
# globalen Exception-Handler; eine unbehandelte Exception ergab Starlettes
# generische, nicht diagnostizierbare Default-Antwort. Jede Anfrage bekommt
# jetzt eine Request-ID (Antwort-Header UND Log-Zeile), über die eine
# Fehlermeldung im Support-Fall mit der passenden Server-Log-Zeile
# zusammengeführt werden kann, ohne dass die Log-Zeile selbst sensible
# Nutzdaten (Anfrage-Body, Cookies, Auth-Header) enthalten muss.
#
# WICHTIG für Abwärtskompatibilität: das Frontend liest bei Fehlern gezielt
# `response.data.detail` (siehe frontend/src/components/common/Toast.tsx).
# Beide Handler unten liefern deshalb weiterhin genau dieses Feld mit
# demselben Inhalt wie zuvor - "request_id" wird nur ERGÄNZT, nichts
# Bestehendes wird umbenannt oder entfernt.


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": request_id},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    # Vollständiger Traceback landet im Server-Log (zur Diagnose), aber NICHT
    # in der Antwort an den Client - eine interne Exception-Message kann
    # unbeabsichtigt interne Pfade, Query-Fragmente oder Bibliotheksdetails
    # enthalten. Anfrage-Body/Header werden hier bewusst NICHT mitgeloggt.
    logger.exception(
        "Unbehandelte Exception bei %s %s (request_id=%s)",
        request.method, request.url.path, request_id,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Ein unerwarteter Fehler ist aufgetreten. Bitte später erneut versuchen.",
            "request_id": request_id,
        },
    )


# ========== Health Check ==========


@app.get("/health", tags=["System"])
async def health_check():
    """
    Health-Check-Endpoint für die Plattform (Render: healthCheckPath).

    Prüft zusätzlich die Datenbankverbindung mit einem leichten SELECT 1
    (Auditbericht, Befund "Betriebsüberwachung": der Check meldete bisher
    unabhängig vom DB-Zustand immer "ok", sodass eine nicht erreichbare
    Datenbank von der Plattform nicht erkannt worden wäre).
    """
    from sqlalchemy import text
    from app.database.engine import engine

    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
        logger.exception("Health-Check: Datenbankverbindung fehlgeschlagen")

    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={
            "status": "ok" if db_ok else "degraded",
            "service": "Authority Matching System",
            "version": "1.0.0",
            "database": "ok" if db_ok else "unreachable",
        },
    )


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
# Priorität 3 des Auditberichts-Folgeberichts, Befund "API-Stabilität": die
# API war komplett unversioniert (nur /api, kein /v1). Additiv gelöst statt
# als Breaking Change: jeder Router wird jetzt unter ZWEI Prefixen montiert -
# /api (unverändert, das bestehende Frontend ruft weiterhin genau das auf,
# siehe frontend/src/services/api.ts) UND /api/v1 (neu, als stabile Basis für
# künftige Systemintegrationen gedacht, siehe API-Key-Zugang in auth.py). Ein
# künftiger /api/v2 könnte parallel dazukommen, ohne /api/v1-Konsumenten zu
# brechen - dafür ist die Liste hier der einzige Ort, der geändert werden muss.

protected = [Depends(require_login)]

_versioned_routers = [
    (auth.router, None),  # öffentlich (Login selbst darf nicht gesperrt sein)
    (buildings.router, protected),
    (authorities.router, protected),
    (request_types.router, protected),
    (matching.router, protected),
    (documents.router, protected),
    (requests_api.router, protected),
    (imports.router, protected),
    (geo.router, protected),
    (jurisdictions.router, protected),
    (data_quality.router, protected),
    (cases.router, protected),
    (data_sources.router, protected),
    (users.router, protected),
]
for router, deps in _versioned_routers:
    kwargs = {"dependencies": deps} if deps else {}
    app.include_router(router, prefix="/api", **kwargs)
    app.include_router(router, prefix="/api/v1", **kwargs)

# Nicht über dependencies=protected: der Inbound-Webhook kann sich nicht per
# Cookie-Session authentisieren (Mailgun ruft ihn direkt auf) und ist
# stattdessen per HMAC-Signatur gesichert; die übrigen Routen darin sind
# einzeln mit require_main abgesichert (deckt "eingeloggt" implizit mit ab).
app.include_router(mailbox_inbound.router, prefix="/api")
app.include_router(mailbox_inbound.router, prefix="/api/v1")

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
