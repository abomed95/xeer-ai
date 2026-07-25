"""Routes d'authentification : inscription, connexion, profil."""
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db, utcnow
from app.deps import get_current_user
from app.ratelimit import rate_limit
from app.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UserOut,
)
from app.security import create_token, hash_password, verify_password
from app.services.accounts import get_user_by_email, user_out

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    # Limite la création de comptes en masse depuis une même adresse.
    dependencies=[Depends(rate_limit("register", limit=5, window_seconds=3600))],
)
def register(payload: RegisterRequest):
    email = payload.email.lower().strip()
    if get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Un compte existe déjà avec cet email.")

    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO users (email, password_hash, full_name, created_at) "
            "VALUES (?, ?, ?, ?)",
            (email, hash_password(payload.password), payload.full_name.strip(), utcnow()),
        )
        user_id = cursor.lastrowid
        user = dict(db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())

    return AuthResponse(token=create_token(user_id), user=UserOut(**user_out(user)))


@router.post(
    "/login",
    response_model=AuthResponse,
    # Ralentit le bruteforce de mots de passe.
    dependencies=[Depends(rate_limit("login", limit=10, window_seconds=300))],
)
def login(payload: LoginRequest):
    user = get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    return AuthResponse(token=create_token(user["id"]), user=UserOut(**user_out(user)))


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return UserOut(**user_out(user))


@router.put("/profile", response_model=UserOut)
def update_profile(payload: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    with get_db() as db:
        db.execute(
            "UPDATE users SET full_name = ? WHERE id = ?",
            (payload.full_name.strip(), user["id"]),
        )
        fresh = dict(db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone())
    return UserOut(**user_out(fresh))


@router.put(
    "/password",
    # Empêche de deviner le mot de passe actuel par essais répétés.
    dependencies=[Depends(rate_limit("change_password", limit=10, window_seconds=600))],
)
def change_password(payload: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    if not verify_password(payload.current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Mot de passe actuel incorrect.")
    with get_db() as db:
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(payload.new_password), user["id"]),
        )
    return {"message": "Mot de passe modifié avec succès."}
