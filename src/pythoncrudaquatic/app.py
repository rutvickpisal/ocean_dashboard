"""FastAPI application composition and lifecycle management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import pool
from .db import settings
from .routes.auth import router as auth_router
from .routes.router import router

tags_metadata = [
    {"name": "Health", "description": "Is the API (and its database) alive?"},
    {"name": "Species", "description": "The creatures themselves: fish, sharks, mammals, molluscs and more."},
    {"name": "Habitats", "description": "Ocean locations where creatures were spotted."},
    {"name": "Observers", "description": "The divers and biologists who report sightings."},
    {"name": "Sightings", "description": "Each sighting links a species, a habitat and an observer (4-table JOIN)."},
    {"name": "Stats", "description": "Summary questions answered with JOINs, GROUP BY and HAVING."},
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Open the connection pool when the app starts and close it when it stops."""
    pool.open(wait=True, timeout=10)
    yield
    pool.close()


app = FastAPI(
    title="Ocean API",
    description="Explore fish and ocean creatures: species, where they live, and who spotted them.",
    version="0.1.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,          # new: lets the browser send the cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(auth_router)
