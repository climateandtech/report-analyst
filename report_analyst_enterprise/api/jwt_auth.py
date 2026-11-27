"""JWT verification for question set admin API."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet, OctKey

from report_analyst.core.installed_questionsets import record_jti

DEFAULT_AUDIENCE = "report-analyst-questionset-admin"
REQUIRED_SCOPE = "questionset:write"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def questionset_admin_configured() -> bool:
    return bool(os.getenv("QUESTIONSETS_JWT_PUBLIC_JWK") or os.getenv("QUESTIONSETS_JWT_HMAC_SECRET"))


def _issuer_allowlist() -> List[str]:
    raw = os.getenv("QUESTIONSETS_JWT_ISSUERS", "")
    return [x.strip() for x in raw.split(",") if x.strip()]


def _load_verify_key():
    secret = os.getenv("QUESTIONSETS_JWT_HMAC_SECRET")
    if secret:
        return OctKey.import_key(secret)

    jwk_json = os.getenv("QUESTIONSETS_JWT_PUBLIC_JWK")
    if jwk_json:
        data = json.loads(jwk_json)
        if "keys" in data:
            return KeySet.import_key_set(data)
        return KeySet.import_key_set({"keys": [data]})

    return None


def verify_admin_jwt(token: str) -> Dict[str, Any]:
    key_set = _load_verify_key()
    if key_set is None:
        raise HTTPException(status_code=503, detail="questionset admin JWT not configured")

    audience = os.getenv("QUESTIONSETS_JWT_AUDIENCE", DEFAULT_AUDIENCE)
    try:
        if isinstance(key_set, OctKey):
            decoded = jwt.decode(token, key_set)
        else:
            decoded = jwt.decode(token, key_set)
    except JoseError as exc:
        raise HTTPException(status_code=401, detail=f"invalid token: {exc}") from exc

    claims: Dict[str, Any] = dict(decoded.claims)

    token_aud = claims.get("aud")
    if isinstance(token_aud, list):
        if audience not in token_aud:
            raise HTTPException(status_code=401, detail="invalid audience")
    elif token_aud != audience:
        raise HTTPException(status_code=401, detail="invalid audience")
    issuers = _issuer_allowlist()
    if issuers and claims.get("iss") not in issuers:
        raise HTTPException(status_code=401, detail="invalid issuer")
    raw_scope = claims.get("scope", "")
    scope_list = raw_scope.split() if isinstance(raw_scope, str) else list(raw_scope)
    if REQUIRED_SCOPE not in scope_list:
        raise HTTPException(status_code=401, detail="missing questionset:write scope")

    jti = claims.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="missing jti")
    exp = claims.get("exp")
    if exp is None:
        raise HTTPException(status_code=401, detail="missing exp")
    expires_at = datetime.fromtimestamp(int(exp), tz=timezone.utc).replace(tzinfo=None)
    if not record_jti(str(jti), expires_at):
        raise HTTPException(status_code=401, detail="token_already_used")
    return claims


async def require_questionset_admin(request: Request) -> Dict[str, Any]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = auth[7:].strip()
    return verify_admin_jwt(token)


def allow_builtin_override(claims: Optional[Dict[str, Any]] = None) -> bool:
    if _env_bool("QUESTIONSET_ALLOW_BUILTIN_OVERRIDE"):
        return True
    if claims and "questionset:override" in str(claims.get("scope", "")):
        return True
    return False