"""Limitation de débit par fenêtre glissante.

Deux risques concrets sans limitation :
* le formulaire de connexion est exposé au bruteforce de mots de passe ;
* chaque appel à `/api/chat/ask` consomme des crédits OpenAI, donc de l'argent
  réel — un client Premium (quota illimité) ou un script peut faire exploser la
  facture.

Les compteurs vivent en mémoire, donc **par instance**. C'est suffisant avec
`instance_count: 1` (la configuration DigitalOcean actuelle). Au-delà, il faudra
un magasin partagé (Redis) pour que la limite soit globale.
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request

from app import config
from app.deps import get_current_user

_hits: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()


def _client_ip(request: Request) -> str:
    """IP de l'appelant, en tenant compte du proxy du PaaS."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        # Le premier élément est l'IP cliente d'origine.
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "inconnu"


def _check(key: str, limit: int, window_seconds: int) -> None:
    now = time.monotonic()
    with _lock:
        timestamps = _hits[key]
        # Purge les appels sortis de la fenêtre.
        while timestamps and now - timestamps[0] > window_seconds:
            timestamps.popleft()
        if len(timestamps) >= limit:
            retry_after = max(1, int(window_seconds - (now - timestamps[0])))
            raise HTTPException(
                status_code=429,
                detail=(
                    "Trop de requêtes. Réessayez dans "
                    f"{retry_after} seconde(s)."
                ),
                headers={"Retry-After": str(retry_after)},
            )
        timestamps.append(now)


def reset() -> None:
    """Vide les compteurs — utilisé par les tests."""
    with _lock:
        _hits.clear()


def rate_limit(name: str, limit: int, window_seconds: int):
    """Dépendance FastAPI limitant par adresse IP.

    `name` isole les compteurs d'une route des autres.
    """

    def dependency(request: Request) -> None:
        if not config.RATE_LIMIT_ENABLED:
            return
        _check(f"{name}:ip:{_client_ip(request)}", limit, window_seconds)

    return dependency


def rate_limit_user(name: str, limit: int, window_seconds: int):
    """Dépendance FastAPI limitant par utilisateur authentifié.

    Renvoie l'utilisateur courant, pour remplacer `get_current_user` sur la
    route sans authentifier deux fois.
    """

    def dependency(user: dict = Depends(get_current_user)) -> dict:
        if config.RATE_LIMIT_ENABLED:
            _check(f"{name}:user:{user['id']}", limit, window_seconds)
        return user

    return dependency
