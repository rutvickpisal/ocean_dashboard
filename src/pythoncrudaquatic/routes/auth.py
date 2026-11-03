"""Authentication HTTP routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import RedirectResponse, Response

from ..controllers.auth_controller import (
    current_user,
    github_callback,
    github_login,
    logout_session,
    refresh_session,
)
from ..schemas import AuthTokenResponse, AuthUser

router = APIRouter(prefix="/auth", tags=["Auth"])
bearer_auth = HTTPBearer(auto_error=False)


@router.get("/github/login", summary="Start GitHub login")
def start_github_login() -> RedirectResponse:
    """Redirect the browser to GitHub's authorization page."""
    return github_login()


@router.get("/github/callback", summary="GitHub sends the user back here")
def finish_github_login(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """Validate GitHub's callback and establish the authenticated session."""
    return github_callback(request, code, state, error)


@router.post(
    "/refresh",
    response_model=AuthTokenResponse,
    responses={401: {"description": "Refresh token is missing, expired, or invalid."}},
    summary="Refresh the access token",
)
def refresh_access_token(request: Request) -> Response:
    """Rotate the refresh-token cookie and return a short-lived access token."""
    return refresh_session(request)


@router.get(
    "/me",
    response_model=AuthUser,
    responses={401: {"description": "Access token is missing, invalid, or expired."}},
    summary="Get the authenticated user",
)
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_auth),
) -> dict:
    """Return the active user's profile for a valid bearer access token."""
    token = credentials.credentials if credentials is not None else None
    return current_user(token)


@router.post(
    "/logout",
    status_code=204,
    responses={403: {"description": "Request origin is not allowed."}},
    summary="Log out",
)
def logout(request: Request) -> Response:
    """Delete the current refresh token and clear its browser cookie."""
    return logout_session(request)
