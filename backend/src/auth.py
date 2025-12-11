# auth_fastapi.py
from __future__ import annotations

import asyncio
import time
import urllib.parse
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union, Callable

import httpx
from fastapi import Cookie, Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from exceptions import APIException, AuthenticationError, AuthorizationError

# Prefer extracting settings to avoid circular imports:
from config import config 
import kutils

# ---------------- Security scheme (shown in Swagger) ----------------
security_scheme_name = "BearerAuth"
bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name=security_scheme_name,
    description="An OAuth2 token issued by the Open-CP IDP.",
)
security_doc = security_scheme_name

# ---------------- HTTP client (pooled) ----------------
_http: httpx.AsyncClient | None = None


def http() -> httpx.AsyncClient:
    global _http
    if _http is None:
        _http = httpx.AsyncClient(timeout=5.0)
    return _http


# ---------------- JWKS cache with retry on unknown kid ----------------
_JWKS: Dict[str, Any] | None = None
_JWKS_TS: float = 0.0
_JWKS_TTL = 600  # seconds


def _jwks_url() -> str:
    return f"{config.settings['KEYCLOAK_URL']}/realms/{config.settings['KEYCLOAK_REALM']}/protocol/openid-connect/certs"


async def _get_jwks(force: bool = False) -> Dict[str, Any]:
    global _JWKS, _JWKS_TS
    now = time.time()
    if not force and _JWKS and (now - _JWKS_TS < _JWKS_TTL):
        return _JWKS
    resp = await http().get(_jwks_url())
    resp.raise_for_status()
    _JWKS = resp.json()
    _JWKS_TS = now
    return _JWKS


# ---------------- Token extraction ----------------
def _extract_bearer_from_header(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError(detail="Authorization header is missing or malformed")
    return parts[1].strip()


def _get_token_from_request(
    request: Request,
    authorization: Optional[str],
    credentials: Optional[HTTPAuthorizationCredentials],
) -> str:
    token = None
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
    if token is None and authorization:
        token = _extract_bearer_from_header(authorization)
    if not token:
        raise AuthenticationError(detail="Bearer token is missing")
    return urllib.parse.unquote(token).strip()


def get_current_token(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    return _get_token_from_request(
        request, authorization, credentials
    )


# ---------------- Local JWT verify (with retry on unknown kid) ----------------
async def api_verify_token(token: str) -> Dict[str, Any]:
    issuer = config.settings["KEYCLOAK_ISSUER_URL"]
    accepted_audiences: List[str] = list(
        config.settings.get("KEYCLOAK_AUDIENCES") or ["master-realm", "account"]
    )

    try:
        jwks = await _get_jwks()
        unverified_header = jwt.get_unverified_header(token)

        def pick_key(jwks_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
            for key in jwks_data.get("keys", []):
                if key.get("kid") == unverified_header.get("kid"):
                    return {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"],
                    }
            return None

        rsa_key = pick_key(jwks)
        # Retry once if unknown kid (rotation)
        if not rsa_key:
            jwks = await _get_jwks(force=True)
            rsa_key = pick_key(jwks)
        if not rsa_key:
            raise AuthenticationError(detail="Signing key not found for provided token")

        last_err: Optional[Exception] = None
        for aud in accepted_audiences:
            try:
                return jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=aud,
                    issuer=issuer,
                )
            except JWTError as e:
                last_err = e
                continue

        raise AuthenticationError(
            detail="Bearer token could not be verified"
        ) from last_err

    except AuthenticationError:
        raise
    except httpx.HTTPError as e:
        raise APIException(
            status_code=502,
            detail="Failed to fetch JWKS from identity provider",
            code="upstream/bad_gateway",
            extra={"title": "BadGatewayError"},
        ) from e
    except JWTError as e:
        raise AuthenticationError(detail="Error decoding token") from e
    except Exception as e:
        raise APIException(
            status_code=500,
            detail="Internal server error during token verification",
            code="server/internal",
            extra={"title": "InternalError"},
        ) from e


# ---------------- Roles / permissions ----------------
def _parse_permissions(perms: Optional[Union[str, Iterable[str]]]) -> List[str]:
    if perms is None:
        return []
    if isinstance(perms, str):
        return [p.strip().lower() for p in perms.split(",") if p.strip()]
    return [str(p).strip().lower() for p in perms if str(p).strip()]


def _extract_roles(payload: Dict[str, Any]) -> List[str]:
    roles: List[str] = []
    realm = payload.get("realm_access") or {}
    roles += realm.get("roles") or []
    resource_access = payload.get("resource_access") or {}
    client_id = getattr(config.settings, "KEYCLOAK_CLIENT_ID", None)
    if client_id and client_id in resource_access:
        roles += resource_access[client_id].get("roles") or []
    else:
        for v in resource_access.values():
            roles += v.get("roles") or []
    return sorted({str(r).strip().lower() for r in roles if r})


def _check_permissions(user_roles: List[str], required: List[str], match: str) -> bool:
    if not required:
        return True
    return (
        all(r in user_roles for r in required)
        if match == "all"
        else any(r in user_roles for r in required)
    )


# ---------------- Introspection cache (short TTL) ----------------
_INTROSPECT_CACHE: Dict[str, Tuple[float, bool]] = {}
_INTROSPECT_TTL = 30  # seconds


async def _introspect_active(token: str) -> None:
    now = time.time()
    hit = _INTROSPECT_CACHE.get(token)
    if hit and (now - hit[0] < _INTROSPECT_TTL):
        if hit[1]:
            return
        raise AuthenticationError(detail="Token inactive")
    # Perform your server-side check (raises if inactive)
    # If kutils is sync, run it in a thread:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, kutils.introspect_token, token)
    _INTROSPECT_CACHE[token] = (now, True)


# ---------------- Unified dependency ----------------
def auth(
    permissions: Optional[Union[str, Iterable[str]]] = None,
    *,
    match: str = "any",  # "any" or "all"
    mode: str = "local",  # "local" | "introspect" | "both"
) -> Callable[..., Dict[str, Any]]:
    required = _parse_permissions(permissions)
    match = (match or "any").lower()
    mode = (mode or "local").lower()

    async def dependency(
        token: str = Depends(get_current_token),
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] | None = None

        if mode in {"local", "both"}:
            payload = await api_verify_token(token)

        if mode in {"introspect", "both"}:
            await _introspect_active(token)
            # If payload is still None (pure introspect), optionally decode to expose claims:
            if payload is None:
                payload = await api_verify_token(token)

        if payload is None:
            raise AuthenticationError(detail="Unsupported auth mode")

        if required:
            roles = _extract_roles(payload)
            if not _check_permissions(roles, required, match):
                raise AuthorizationError(
                    detail="Insufficient permissions",
                    extra={"required": required, "match": match, "roles": roles},
                )
        return payload

    return dependency