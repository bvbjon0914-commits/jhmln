"""
API Routes: Auth (Login-Gate)
"""

import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import COOKIE_SECURE, LOGIN_RATE_LIMIT_WINDOW_SECONDS
from app.database import get_db_session
from app.models.settings import AppSettings
from app.models.user import User
from app.schemas import UserRegisterCreate
from app.services import rate_limiter
from app.services.auth import (
    COOKIE_NAME,
    check_api_key,
    check_password,
    check_user_credentials,
    create_token,
    hash_password,
    verify_token,
)

API_KEY_HEADER = "X-API-Key"

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
    email: Optional[str] = None


class LoginRequiredPayload(BaseModel):
    enabled: bool


def _current_session(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return verify_token(token)


def require_login(request: Request, db: Session = Depends(get_db_session)) -> None:
    """
    FastAPI-Dependency: sperrt eine Route, außer login_required ist deaktiviert.

    Akzeptiert ZUSÄTZLICH zum Cookie-Login einen X-API-Key-Header (siehe
    check_api_key) - getrennter Zugang für Systemintegrationen statt eines
    geteilten Menschen-Passworts (Auditbericht-Folgebericht, Priorität 3,
    Befund "M2M-Zugriff"). Ein gültiger API-Key gilt unabhängig vom
    login_required-Schalter, der nur die Browser-Login-Pflicht für Menschen
    steuert - ein System, das einen Schlüssel besitzt, soll nicht davon
    abhängen, ob gerade jemand den UI-Login ein-/ausgeschaltet hat.
    """
    if check_api_key(request.headers.get(API_KEY_HEADER, "")):
        return

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


def get_current_user(request: Request, db: Session = Depends(get_db_session)) -> Optional[User]:
    """
    FastAPI-Dependency: liefert das volle Profil des eingeloggten
    Nutzer-Accounts, oder None (Login per API-Key, per Legacy-Passwort ohne
    User-Zeile, oder gar nicht eingeloggt). Sperrt NICHT - Routen, die
    zwingend einen echten User brauchen, muessen selbst pruefen.
    """
    session = _current_session(request)
    if not session or not session.get("user_id"):
        return None
    return db.query(User).filter(User.user_id == session["user_id"]).first()


@router.get("/auth/status", tags=["Auth"])
def auth_status(request: Request, db: Session = Depends(get_db_session)):
    """Öffentlich: sagt dem Frontend, ob ein Login-Screen gezeigt werden muss."""
    settings = AppSettings.get_or_create(db)
    session = _current_session(request)
    user = None
    if session and session.get("user_id"):
        user = db.query(User).filter(User.user_id == session["user_id"]).first()
    return {
        "login_required": settings.login_required,
        "logged_in": session is not None,
        "is_main": bool(session and session.get("is_main")),
        "user": user.to_dict() if user else None,
    }


@router.post("/auth/login", tags=["Auth"])
def login(payload: LoginPayload, request: Request, response: Response, db: Session = Depends(get_db_session)):
    """
    Öffentlich: prüft die Anmeldedaten und setzt bei Erfolg das Session-Cookie.

    Zwei Wege: mit `email` wird gegen die `users`-Tabelle geprueft
    (check_user_credentials); ohne `email` greift unveraendert der alte
    Zwei-Passwoerter-Weg (check_password) - bewusst als dauerhafter
    Fallback erhalten, siehe app/services/auth.py Modul-Docstring.
    """
    client_key = _client_key(request)
    if rate_limiter.is_blocked(client_key):
        raise HTTPException(
            status_code=429,
            detail="Zu viele fehlgeschlagene Login-Versuche. Bitte später erneut versuchen.",
            headers={"Retry-After": str(LOGIN_RATE_LIMIT_WINDOW_SECONDS)},
        )

    user: Optional[User] = None
    if payload.email:
        user = check_user_credentials(db, payload.email, payload.password)
        if user is None:
            rate_limiter.record_failure(client_key)
            raise HTTPException(status_code=401, detail="E-Mail oder Passwort falsch.")
        is_main = user.is_main
    else:
        kind = check_password(payload.password)
        if kind is None:
            rate_limiter.record_failure(client_key)
            raise HTTPException(status_code=401, detail="Falsches Passwort.")
        is_main = kind == "main"

    rate_limiter.record_success(client_key)
    if user is not None:
        user.last_login_at = datetime.utcnow()
        db.commit()
    token = create_token(is_main, user_id=user.user_id if user else None)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=60 * 60 * 24 * 30,
    )
    return {"is_main": is_main, "user": user.to_dict() if user else None}


@router.post("/auth/register", status_code=201, tags=["Auth"])
def register(payload: UserRegisterCreate, request: Request, db: Session = Depends(get_db_session)):
    """
    Öffentlich (bewusst OHNE require_login/require_main - für anonyme
    Besucher): Selbstregistrierung eines neuen Nutzer-Accounts.

    Der angelegte Account ist zunaechst NUR ein Datensatz mit
    status="pending" und active=False - er kann sich NICHT einloggen
    (check_user_credentials filtert auf active=True) und bekommt hier
    bewusst KEIN Session-Cookie gesetzt. Erst ein Admin (POST
    /users/{user_id}/approve) schaltet ihn frei. is_main/active/status
    kommen deshalb nie aus dem Request, sondern werden hier hart gesetzt.
    """
    client_key = _client_key(request)
    if rate_limiter.is_blocked(client_key):
        raise HTTPException(
            status_code=429,
            detail="Zu viele Registrierungsversuche. Bitte später erneut versuchen.",
            headers={"Retry-After": str(LOGIN_RATE_LIMIT_WINDOW_SECONDS)},
        )

    email = payload.email.strip().lower()
    # Bewusst UNABHAENGIG vom status pruefen (pending/active/rejected) - eine
    # E-Mail darf nur einen Account-Datensatz haben. Die Fehlermeldung bleibt
    # absichtlich generisch, um den konkreten Status nicht nach aussen zu
    # verraten (kein User-Enumeration-artiges Informationsleck).
    if db.query(User).filter(User.email == email).first():
        rate_limiter.record_failure(client_key)
        raise HTTPException(status_code=409, detail="Für diese E-Mail-Adresse existiert bereits ein Account.")

    user = User(
        user_id=f"USR-{secrets.token_hex(6)}",
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        function=payload.function,
        street=payload.street,
        house_number=payload.house_number,
        postal_code=payload.postal_code,
        city=payload.city,
        is_main=False,
        active=False,
        status="pending",
    )
    db.add(user)
    db.commit()
    rate_limiter.record_success(client_key)

    return {
        "status": "pending",
        "message": "Dein Account wurde angelegt und wartet auf Freigabe durch einen Administrator.",
    }


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


@router.post("/auth/login-required/enable", tags=["Auth"])
def enable_login_required(payload: LoginPayload, request: Request, db: Session = Depends(get_db_session)):
    """
    Öffentlich (bewusst OHNE require_login/require_main): schaltet den
    Login-Zwang WIEDER EIN. Nötig, weil bei ausgeschaltetem Login-Zwang weder
    ein Login-Screen noch eine Haupt-Session existiert und der Schalter sonst
    nicht mehr aus der Oberfläche heraus zurückgestellt werden könnte.

    Kann den Zwang ausschließlich einschalten (nie aus) und ist idempotent.
    Autorisierung: mit `email` muss es ein Haupt-Account (is_main) mit
    passendem Passwort sein, ohne `email` das alte Haupt-Passwort. Jede andere
    Konstellation (falsches Passwort, Nicht-Haupt-Account, geteiltes Passwort)
    ergibt dieselbe generische 401-Antwort. Es wird KEIN Session-Cookie gesetzt.
    """
    client_key = _client_key(request)
    if rate_limiter.is_blocked(client_key):
        raise HTTPException(
            status_code=429,
            detail="Zu viele fehlgeschlagene Login-Versuche. Bitte später erneut versuchen.",
            headers={"Retry-After": str(LOGIN_RATE_LIMIT_WINDOW_SECONDS)},
        )

    if payload.email:
        user = check_user_credentials(db, payload.email, payload.password)
        authorized = user is not None and user.is_main
    else:
        authorized = check_password(payload.password) == "main"

    if not authorized:
        rate_limiter.record_failure(client_key)
        raise HTTPException(status_code=401, detail="Anmeldedaten oder Berechtigung ungültig.")

    rate_limiter.record_success(client_key)
    settings = AppSettings.get_or_create(db)
    settings.login_required = True
    db.commit()
    return {"login_required": True}
