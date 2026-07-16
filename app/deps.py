"""Dépendances FastAPI : authentification et rôles."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security import decode_token
from app.services.accounts import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentification requise.")
    user_id = decode_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Jeton invalide ou expiré.")
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable.")
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès administrateur requis.")
    return user
