"""GitHub OAuth workflow and refresh-token creation."""

import hashlib
import base64
import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from ..db import settings
from ..repositories.auth_repository import (
    create_refresh_token,
    delete_refresh_token,
    get_active_user,
    rotate_refresh_token,
    upsert_github_user,
)

GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
REFRESH_DAYS = 7
ACCESS_TOKEN_MINUTES = 15


class GitHubLoginError(Exception):
    """Raised when GitHub rejects the OAuth authorization code."""


class AccountDisabledError(Exception):
    """Raised when the matched local account is inactive."""


class InvalidRefreshTokenError(Exception):
    """Raised when a refresh token is missing, expired, used, or belongs to a disabled account."""


class InvalidAccessTokenError(Exception):
    """Raised when an access token is malformed, invalid, expired, or no longer authorized."""


def hash_token(token: str) -> str:
    """Store refresh tokens as hashes instead of plaintext."""
    return hashlib.sha256(token.encode()).hexdigest()


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    header = _base64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _base64url(
        json.dumps(
            {
                "sub": str(user_id),
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
                "token_type": "access",
            },
            separators=(",", ":"),
        ).encode()
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = hmac.new(settings.jwt_secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{_base64url(signature)}"


def get_authenticated_user(access_token: str | None) -> dict[str, Any]:
    if not access_token:
        raise InvalidAccessTokenError

    try:
        encoded_header, encoded_payload, encoded_signature = access_token.split(".")
        header_bytes = base64.urlsafe_b64decode(encoded_header + "=" * (-len(encoded_header) % 4))
        payload_bytes = base64.urlsafe_b64decode(encoded_payload + "=" * (-len(encoded_payload) % 4))
        header = json.loads(header_bytes)
        claims = json.loads(payload_bytes)
        signature = base64.urlsafe_b64decode(encoded_signature + "=" * (-len(encoded_signature) % 4))

        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise InvalidAccessTokenError
        signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
        expected_signature = hmac.new(settings.jwt_secret.encode(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_signature):
            raise InvalidAccessTokenError

        user_id = int(claims["sub"])
        expires_at = claims["exp"]
        if (
            claims.get("token_type") != "access"
            or user_id < 1
            or isinstance(expires_at, bool)
            or not isinstance(expires_at, (int, float))
            or expires_at <= datetime.now(timezone.utc).timestamp()
        ):
            raise InvalidAccessTokenError
    except (ValueError, TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidAccessTokenError from exc

    user = get_active_user(user_id)
    if user is None:
        raise InvalidAccessTokenError
    return user


def logout_session(refresh_token: str | None) -> None:
    if refresh_token:
        delete_refresh_token(hash_token(refresh_token))


def refresh_session(refresh_token: str | None) -> tuple[str, str]:
    if not refresh_token:
        raise InvalidRefreshTokenError

    replacement_token = secrets.token_urlsafe(48)
    user = rotate_refresh_token(
        current_token_hash=hash_token(refresh_token),
        replacement_token_hash=hash_token(replacement_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS),
    )
    if user is None:
        raise InvalidRefreshTokenError

    access_token = create_access_token(user["user_id"])
    return replacement_token, access_token


def complete_github_login(code: str) -> str:
    token_res = httpx.post(
        GITHUB_TOKEN_URL,
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )
    github_token = token_res.json().get("access_token")
    if not github_token:
        raise GitHubLoginError

    profile: dict[str, Any] = httpx.get(
        GITHUB_USER_URL,
        headers={
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=10,
    ).json()

    user = upsert_github_user(
        provider_id=str(profile["id"]),
        username=profile["login"],
        email=profile.get("email"),
        avatar_url=profile.get("avatar_url"),
    )
    if not user["is_active"]:
        raise AccountDisabledError

    raw_token = secrets.token_urlsafe(48)
    create_refresh_token(
        user_id=user["id"],
        family_id=uuid.uuid4(),
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS),
    )
    return raw_token
