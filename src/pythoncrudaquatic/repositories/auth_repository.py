"""Database operations for authentication."""

from datetime import datetime
from typing import Any
from uuid import UUID

from ..db import fetch_one


def upsert_github_user(
    provider_id: str,
    username: str,
    email: str | None,
    avatar_url: str | None,
) -> dict[str, Any]:
    user = fetch_one(
        """
        INSERT INTO users (provider, provider_id, username, email, avatar_url)
        VALUES ('github', %(pid)s, %(username)s, %(email)s, %(avatar)s)
        ON CONFLICT (provider, provider_id) DO UPDATE
            SET username   = EXCLUDED.username,
                email      = COALESCE(EXCLUDED.email, users.email),
                avatar_url = EXCLUDED.avatar_url
        RETURNING id, is_active
        """,
        {
            "pid": provider_id,
            "username": username,
            "email": email,
            "avatar": avatar_url,
        },
    )
    if user is None:
        raise RuntimeError("GitHub user upsert returned no user.")
    return user


def create_refresh_token(
    user_id: int,
    family_id: UUID,
    token_hash: str,
    expires_at: datetime,
) -> None:
    fetch_one(
        """
        INSERT INTO refresh_tokens (user_id, family_id, token_hash, expires_at)
        VALUES (%(user_id)s, %(family)s, %(hash)s, %(expires)s)
        RETURNING id
        """,
        {
            "user_id": user_id,
            "family": family_id,
            "hash": token_hash,
            "expires": expires_at,
        },
    )


def rotate_refresh_token(
    current_token_hash: str,
    replacement_token_hash: str,
    expires_at: datetime,
) -> dict[str, Any] | None:
    """Atomically replace a valid token hash, allowing each refresh token once."""
    return fetch_one(
        """
        UPDATE refresh_tokens AS token
        SET token_hash = %(replacement_hash)s,
            expires_at = %(expires_at)s
        FROM users AS account
        WHERE token.user_id = account.id
          AND token.token_hash = %(current_hash)s
          AND token.expires_at > now()
          AND account.is_active
        RETURNING token.user_id, token.family_id
        """,
        {
            "current_hash": current_token_hash,
            "replacement_hash": replacement_token_hash,
            "expires_at": expires_at,
        },
    )


def get_active_user(user_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, username, email, avatar_url
        FROM users
        WHERE id = %(id)s AND is_active
        """,
        {"id": user_id},
    )


def delete_refresh_token(token_hash: str) -> None:
    fetch_one(
        "DELETE FROM refresh_tokens WHERE token_hash = %(token_hash)s RETURNING id",
        {"token_hash": token_hash},
    )
