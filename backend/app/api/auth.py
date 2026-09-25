"""
API Routes: Auth (Login-Gate)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import COOKIE_SECURE, LOGIN_RATE_LIMIT_WINDOW_SECONDS
from app.database import get_db_session
from app.models.settings import AppSettings
from app.services import rate_limiter
from app.services.auth import COOKIE_NAME, check_password, create_token, verify_token

router = APIRouter()


def _client_key(request: Request) -> str:
    """Bewusst die rohe Client-IP als Schlüssel, kein X-Forwarded-For-Parsing:
    dieser Header ließe sich vom Anfragenden selbst gegen unbeteiligte Dritte
    fälschen, solange kein vertrauenswürdiger, konfigurierter Reverse-Proxy
    zwischengeschaltet ist. Damit begrenzt dies aktuell in erster Linie einen
    einzelnen Client, nicht zuverlässig eine Quelle hinter einem Proxy."""
    return request.client.host if request.client else "unknown"


class LoginPayload(BaseModel):
    password: str


class LoginRequiredPayload(BaseModel):
    enabled: bool


def _current_session(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return verify_token(token)


def require_login(request: Request, db: Session = Depends(get_db_session)) -> None:
    """FastAPI-Dependency: sperrt eine Route, außer login_required ist deaktiviert."""
    settings = AppSettings.get_or_create(db)
    if not settings.login_required:
        return

    session = _current_session(request)
    if session is None:
        raise HTTPException(status_code=401, detail="Login erforderlich")


def require_main(request: Request, db: Session = Depends(get_db_session)) -> None:
    """FastAPI-Dependency: nur für den Haupt-Account, unabhängig von login_required."""
    session = _current_session(request)
    if session is None or not session.get("is_main"):
        raise HTTPException(status_code=403, detail="Nur der Haupt-Account darf das.")


def get_is_main(request: Request) -> bool:
    """
    FastAPI-Dependency, die (im Gegensatz zu require_main) NICHT sperrt –
    für Routen, die für alle nutzbar sind, aber einzelne Zusatzoptionen
    nur dem Haupt-Account erlauben sollen.
    """
    session = _current_session(request)
    return bool(session and session.get("is_main"))


@router.get("/auth/status", tags=["Auth"])
def auth_status(request: Request, db: Session = Depends(get_db_session)):
    """Öffentlich: sagt dem Frontend, ob ein Login-Screen gezeigt werden muss."""
    settings = AppSettings.get_or_create(db)
    session = _current_session(request)
    return {
        "login_required": settings.login_required,
        "logged_in": session is not None,
        "is_main": bool(session and session.get("is_main")),
    }


@router.post("/auth/login", tags=["Auth"])
def login(payload: LoginPayload, request: Request, response: Response):
    """Öffentlich: prüft das Passwort und setzt bei Erfolg das Session-Cookie."""
    client_key = _client_key(request)
    if rate_limiter.is_blocked(client_key):
        raise HTTPException(
            status_code=429,
            detail="Zu viele fehlgeschlagene Login-Versuche. Bitte später erneut versuchen.",
            headers={"Retry-After": str(LOGIN_RATE_LIMIT_WINDOW_SECONDS)},
        )

    kind = check_password(payload.password)
    if kind is None:
        rate_limiter.record_failure(client_key)
        raise HTTPException(status_code=401, detail="Falsches Passwort.")

    rate_limiter.record_success(client_key)
    is_main = kind == "main"
    token = create_token(is_main)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=60 * 60 * 24 * 30,
    )
    return {"is_main": is_main}


@router.post("/auth/logout", tags=["Auth"])
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.put("/auth/settings/login-required", tags=["Auth"])
def set_login_required(
    payload: LoginRequiredPayload,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_main),
):
    """Nur Haupt-Account: schaltet den Login-Zwang für alle an oder aus."""
    settings = AppSettings.get_or_create(db)
    settings.login_required = payload.enabled
    db.commit()
    return {"login_required": settings.login_required}
