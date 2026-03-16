"""
Clerk JWT authentication middleware.

On startup: fetches JWKS from CLERK_JWKS_URL.
Per request: validates Authorization: Bearer <token> (RS256),
injects clerk_user_id (from 'sub' claim) into request.state.
Public paths (no auth required): /health, /docs, /openapi.json, /redoc.
"""
import json
import logging
import urllib.request
from typing import Callable

import jwt
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class ClerkAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, jwks_url: str = "") -> None:
        super().__init__(app)
        self._jwks_url = jwks_url
        self._jwks: dict | None = None
        if jwks_url:
            self._load_jwks()

    def _load_jwks(self) -> None:
        try:
            with urllib.request.urlopen(self._jwks_url, timeout=10) as resp:
                self._jwks = json.loads(resp.read())
            logger.info("JWKS loaded from %s", self._jwks_url)
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to load JWKS: %s", exc)
            self._jwks = None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401, content={"error": {"code": "UNAUTHORIZED"}}
            )

        token = auth_header[len("Bearer "):]

        if not self._jwks:
            # No JWKS configured (test/dev without Clerk) — try decode without verify
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                request.state.clerk_user_id = payload.get("sub", "")
                request.state.email = payload.get("email", "")
                return await call_next(request)
            except Exception:
                return JSONResponse(
                    status_code=401, content={"error": {"code": "UNAUTHORIZED"}}
                )

        try:
            jwks_client = jwt.PyJWKClient.__new__(jwt.PyJWKClient)
            # Use the cached JWKS data
            signing_key = self._get_signing_key(token)
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
            request.state.clerk_user_id = payload["sub"]
            request.state.email = payload.get("email", "")
        except Exception:
            return JSONResponse(
                status_code=401, content={"error": {"code": "UNAUTHORIZED"}}
            )


        return await call_next(request)

    def _get_signing_key(self, token: str):
        """Extract the signing key from cached JWKS by matching kid."""
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not self._jwks:
            raise ValueError("No JWKS available")
        for key_data in self._jwks.get("keys", []):
            if key_data.get("kid") == kid:
                return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_data))
        raise ValueError(f"No key found for kid={kid}")
