"""Compatibility entry point for running the API with ``uvicorn main:app``."""

from pythoncrudaquatic.app import app

__all__ = ["app"]
