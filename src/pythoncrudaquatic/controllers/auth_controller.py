"""HTTP-level handling for authentication routes."""

import secrets
from urllib.parse import urlencode

from fastapi import HTTPException, Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from ..db import settings
from ..services.auth_service import (
    ACCESS_TOKEN_MINUTES,
    AccountDisabledError,
    InvalidAccessTokenError,
    GitHubLoginError,
    InvalidRefreshTokenError,
    complete_github_login,
    get_authenticated_user,
    logout_session as logout_auth_session,
    refresh_session as refresh_auth_session,
)

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"


def check_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") != settings.frontend_url.rstrip("/"):
        raise HTTPException(status_code=403, detail="Request from an untrusted origin.")


def current_user(access_token: str | None) -> dict:
    try:
        return get_authenticated_user(access_token)
    except InvalidAccessTokenError as exc:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def logout_session(request: Request) -> Response:
    check_origin(request)
    logout_auth_session(request.cookies.get("refresh_token"))
    response = Response(status_code=204)
    response.delete_cookie(
        "refresh_token",
        path="/auth",
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )
    return response


def github_login() -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    params = {"client_id": settings.github_client_id, "scope": "read:user", "state": state}
    response = RedirectResponse(f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}")
    response.set_cookie(
        "oauth_state",
        state,
        max_age=600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/auth",
    )
    return response


def github_callback(
    request: Request,
    code: str | None,
    state: str | None,
    error: str | None,
) -> RedirectResponse:
    if error:
        return RedirectResponse(f"{settings.frontend_url}/?login=cancelled")

    saved_state = request.cookies.get("oauth_state")
    if not (code and state and saved_state and secrets.compare_digest(state, saved_state)):
        raise HTTPException(status_code=400, detail="Invalid login state. Please try logging in again.")

    try:
        raw_token = complete_github_login(code)
    except AccountDisabledError as exc:
        raise HTTPException(status_code=403, detail="This account is disabled.") from exc
    except GitHubLoginError as exc:
        raise HTTPException(status_code=400, detail="GitHub did not accept the login code.") from exc

    response = RedirectResponse(settings.frontend_url)
    response.set_cookie(
        "refresh_token",
        raw_token,
        max_age=7 * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/auth",
    )
    response.delete_cookie("oauth_state", path="/auth")
    return response


def refresh_session(request: Request) -> Response:
    check_origin(request)
    try:
        refresh_token, access_token = refresh_auth_session(request.cookies.get("refresh_token"))
    except InvalidRefreshTokenError:
        response = JSONResponse(
            status_code=401,
            content={"detail": "Refresh token is missing, expired, or invalid. Please log in again."},
        )
        response.delete_cookie(
            "refresh_token",
            path="/auth",
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
        )
        return response

    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_MINUTES * 60,
        }
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=7 * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/auth",
    )
    return response
