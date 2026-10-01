"""
API Routes: Users (Nutzerverwaltung)

Admin-only CRUD fuer echte Nutzer-Accounts - jede Route einzeln per
require_main geschuetzt (gleiches Muster wie cases.py/mailbox_inbound.py),
statt am Router-Mount in main.py, da dies bewusst eine reine
Admin-Funktion ist.
"""

import secrets
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, require_login, require_main
from app.database import get_db_session
from app.models.user import User
from app.schemas import UserCreate, UserResponse, UserSelfUpdate, UserUpdate
from app.services.auth import COOKIE_NAME, hash_password

router = APIRouter()


@router.get("/users", response_model=List[UserResponse], tags=["Users"])
def list_users(
    response: Response,
    active_only: bool = False,
    status: Optional[str] = None,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_main),
):
    """Listet Nutzer-Accounts. `status` filtert zusaetzlich (nicht statt)
    `active_only` auf "pending"/"active"/"rejected" - ohne Angabe unveraendertes
    Verhalten wie bisher."""
    query = db.query(User)
    if active_only:
        query = query.filter(User.active.is_(True))
    if status is not None:
        query = query.filter(User.status == status)
    response.headers["X-Total-Count"] = str(query.count())
    return query.order_by(User.full_name).all()


# Die drei "me"-Routen muessen VOR "/users/{user_id}" stehen, sonst wuerde
# FastAPI "me" als user_id in den parametrisierten Routen matchen statt in
# diesen eigenen, require_login- statt require_main-geschuetzten Routen.


@router.get("/users/me", response_model=UserResponse, tags=["Users"])
def get_my_account(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_login),
):
    """Liefert den eigenen Account - fuer jeden eingeloggten Nutzer, nicht nur Admins."""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Login erforderlich")
    return current_user


@router.put("/users/me", response_model=UserResponse, tags=["Users"])
def update_my_account(
    payload: UserSelfUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_login),
):
    """
    Selbstbearbeitung des eigenen Accounts. Bewusst kein is_main/active/status
    im Schema - die eigene Rolle/Freigabe kann ein Nutzer nie selbst aendern.
    Ein Passwortfeld wird nur bei Angabe gehasht und ersetzt.
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Login erforderlich")

    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    data = payload.model_dump(exclude_unset=True, exclude={"password"})
    if "email" in data:
        candidate_email = data["email"].strip().lower()
        existing = db.query(User).filter(User.email == candidate_email, User.user_id != user.user_id).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"E-Mail {candidate_email} ist bereits vergeben")
        data["email"] = candidate_email

    for field, value in data.items():
        setattr(user, field, value)
    if payload.password:
        user.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/me", status_code=204, tags=["Users"])
def delete_my_account(
    response: Response,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_login),
):
    """
    Loescht den eigenen Account unwiderruflich (blockiert, wenn es der letzte
    aktive Haupt-Account waere - gleiche Schutzregel wie beim Admin-Loeschen
    durch Dritte) und meldet die Session direkt mit ab.
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Login erforderlich")

    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if user.is_main:
        remaining_mains = (
            db.query(User)
            .filter(User.is_main.is_(True), User.active.is_(True), User.user_id != user.user_id)
            .count()
        )
        if remaining_mains == 0:
            raise HTTPException(
                status_code=400,
                detail="Der letzte aktive Haupt-Account kann nicht geloescht werden.",
            )

    db.delete(user)
    db.commit()
    response.delete_cookie(COOKIE_NAME)
    return None


@router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: str, db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """Holt die Details eines Nutzer-Accounts."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Nutzer {user_id} nicht gefunden")
    return user


@router.post("/users", response_model=UserResponse, status_code=201, tags=["Users"])
def create_user(payload: UserCreate, db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """Legt einen neuen Nutzer-Account an."""
    email = payload.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail=f"E-Mail {email} ist bereits vergeben")

    data = payload.model_dump(exclude={"password", "email"})
    user = User(
        user_id=f"USR-{secrets.token_hex(6)}",
        email=email,
        password_hash=hash_password(payload.password),
        # Admin-angelegte Accounts sind sofort vertrauenswuerdig, nie
        # "pending" (das gilt nur fuer die oeffentliche Selbstregistrierung,
        # siehe POST /auth/register) - UserCreate hat deshalb kein status-Feld,
        # das muss hier im Code gesetzt werden statt aus dem Payload zu kommen.
        status="active",
        **data,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/approve", response_model=UserResponse, tags=["Users"])
def approve_user(
    user_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_main),
):
    """Gibt einen selbstregistrierten ("pending") Account frei: schaltet ihn
    aktiv und merkt sich, welcher Admin das getan hat (Audit)."""
    if current_user is None:
        # Sollte dank require_main nicht vorkommen, defensiv trotzdem geprueft.
        raise HTTPException(status_code=401, detail="Login erforderlich")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Nutzer {user_id} nicht gefunden")
    if user.status != "pending":
        raise HTTPException(status_code=409, detail="Dieser Account wartet nicht auf Freigabe.")

    user.status = "active"
    user.active = True
    user.reviewed_by = current_user.user_id
    user.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reject", response_model=UserResponse, tags=["Users"])
def reject_user(
    user_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_main),
):
    """Lehnt einen selbstregistrierten ("pending") Account ab. Die Zeile wird
    NICHT geloescht (Audit/Historie), bleibt aber dauerhaft inaktiv."""
    if current_user is None:
        # Sollte dank require_main nicht vorkommen, defensiv trotzdem geprueft.
        raise HTTPException(status_code=401, detail="Login erforderlich")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Nutzer {user_id} nicht gefunden")
    if user.status != "pending":
        raise HTTPException(status_code=409, detail="Dieser Account wartet nicht auf Freigabe.")

    user.status = "rejected"
    user.active = False
    user.reviewed_by = current_user.user_id
    user.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_main),
):
    """
    Aktualisiert einen Nutzer-Account. Ein Passwortfeld wird nur bei Angabe
    gehasht und ersetzt - leer/weggelassen laesst das bestehende Passwort
    unveraendert.
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Nutzer {user_id} nicht gefunden")

    data = payload.model_dump(exclude_unset=True, exclude={"password"})
    if "email" in data:
        candidate_email = data["email"].strip().lower()
        existing = db.query(User).filter(User.email == candidate_email, User.user_id != user_id).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"E-Mail {candidate_email} ist bereits vergeben")
        data["email"] = candidate_email

    would_lose_last_main = (
        user.is_main
        and ("is_main" in data and not data["is_main"] or "active" in data and not data["active"])
    )
    if would_lose_last_main:
        remaining_mains = (
            db.query(User)
            .filter(User.is_main.is_(True), User.active.is_(True), User.user_id != user_id)
            .count()
        )
        if remaining_mains == 0:
            raise HTTPException(
                status_code=400,
                detail="Der letzte aktive Haupt-Account kann nicht deaktiviert/degradiert werden.",
            )

    for field, value in data.items():
        setattr(user, field, value)
    if payload.password:
        user.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204, tags=["Users"])
def delete_user(user_id: str, db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """Löscht einen Nutzer-Account (blockiert das Löschen des letzten Haupt-Accounts)."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Nutzer {user_id} nicht gefunden")

    if user.is_main:
        remaining_mains = (
            db.query(User)
            .filter(User.is_main.is_(True), User.active.is_(True), User.user_id != user_id)
            .count()
        )
        if remaining_mains == 0:
            raise HTTPException(status_code=400, detail="Der letzte aktive Haupt-Account kann nicht gelöscht werden.")

    db.delete(user)
    db.commit()
    return None
