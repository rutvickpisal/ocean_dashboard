"""FastAPI routes: HTTP parameters, response models, and OpenAPI metadata."""

from typing import Annotated

from fastapi import APIRouter, Query

from ..controllers import controller as controllers
from ..schemas import (
    Habitat,
    HabitatSpecies,
    Observer,
    OceanThreatSummary,
    SightingDetail,
    Species,
    SpeciesCount,
    SpeciesSummary,
    SpeciesHabitat,
    TopHabitat,
    TopObserver,
)

router = APIRouter()

Limit = Annotated[int, Query(ge=1, le=100, description="How many rows to return (max 100).")]
Offset = Annotated[int, Query(ge=0, description="How many rows to skip. Page 2 with limit=20 is offset=20.")]
TopN = Annotated[int, Query(ge=1, le=50, description="How many top results to return (max 50).")]


@router.get("/health", tags=["Health"], summary="Check the API and database are up")
def health():
    """Confirm the API is running and can reach Postgres."""
    return controllers.health()


@router.get("/species", response_model=list[Species], tags=["Species"], summary="List species")
def list_species(
    limit: Limit = 20,
    offset: Offset = 0,
    category: Annotated[
        str | None,
        Query(description="Only this category. One of: Fish, Shark, Ray, Mammal, Reptile, Mollusc, Cnidarian, Crustacean, Echinoderm."),
    ] = None,
    conservation_status: Annotated[
        str | None,
        Query(description="Only this status. One of: Least Concern, Near Threatened, Vulnerable, Endangered, Critically Endangered."),
    ] = None,
):
    """Return a page of species, optionally filtered by category or conservation status."""
    return controllers.list_species(limit, offset, category, conservation_status)


@router.get(
    "/species/{species_id}",
    response_model=Species,
    tags=["Species"],
    summary="Get one species by ID",
    responses={404: {"description": "No species with that ID."}},
)
def get_species(species_id: int):
    """Return the full details of a single species."""
    return controllers.get_species(species_id)


@router.get(
    "/species/{species_id}/habitats",
    response_model=list[SpeciesHabitat],
    tags=["Species"],
    summary="Where has this species been seen?",
    responses={404: {"description": "No species with that ID."}},
)
def get_species_habitats(species_id: int, limit: Limit = 20, offset: Offset = 0):
    """List habitats where this species was spotted, with sighting and individual counts."""
    return controllers.list_species_habitats(species_id, limit, offset)


@router.get("/habitats", response_model=list[Habitat], tags=["Habitats"], summary="List habitats")
def list_habitats(
    limit: Limit = 20,
    offset: Offset = 0,
    ocean: Annotated[str | None, Query(description="Only this ocean: Pacific, Atlantic, Indian, Southern or Arctic.")] = None,
    depth_zone: Annotated[
        str | None,
        Query(description="Only this zone: Intertidal, Coral Reef, Open Ocean, Continental Shelf, Deep Sea or Abyssal."),
    ] = None,
):
    """Return a page of ocean locations, optionally filtered by ocean or depth zone."""
    return controllers.list_habitats(limit, offset, ocean, depth_zone)


@router.get(
    "/habitats/{habitat_id}",
    response_model=Habitat,
    tags=["Habitats"],
    summary="Get one habitat by ID",
    responses={404: {"description": "No habitat with that ID."}},
)
def get_habitat(habitat_id: int):
    """Return the details of a single habitat."""
    return controllers.get_habitat(habitat_id)


@router.get(
    "/habitats/{habitat_id}/species",
    response_model=list[HabitatSpecies],
    tags=["Habitats"],
    summary="Which species live here?",
    responses={404: {"description": "No habitat with that ID."}},
)
def get_habitat_species(habitat_id: int, limit: Limit = 20, offset: Offset = 0):
    """List species seen at this habitat, most-seen first."""
    return controllers.list_habitat_species(habitat_id, limit, offset)


@router.get("/observers", response_model=list[Observer], tags=["Observers"], summary="List observers")
def list_observers(
    limit: Limit = 20,
    offset: Offset = 0,
    country: Annotated[str | None, Query(description="Only observers from this country, e.g. India.")] = None,
):
    """Return a page of observers, optionally filtered by country."""
    return controllers.list_observers(limit, offset, country)


@router.get(
    "/sightings",
    response_model=list[SightingDetail],
    tags=["Sightings"],
    summary="Recent sightings (with names)",
)
def list_sightings(
    limit: Limit = 20,
    offset: Offset = 0,
    species_id: Annotated[int | None, Query(description="Only sightings of this species ID.")] = None,
    habitat_id: Annotated[int | None, Query(description="Only sightings at this habitat ID.")] = None,
    observer_id: Annotated[int | None, Query(description="Only sightings reported by this observer ID.")] = None,
):
    """Return sightings newest first, with readable species, habitat, and observer names."""
    return controllers.list_sightings(limit, offset, species_id, habitat_id, observer_id)


@router.get(
    "/stats/top-habitats",
    response_model=list[TopHabitat],
    tags=["Stats"],
    summary="Most biodiverse habitats",
)
def top_habitats(limit: TopN = 10):
    """Rank habitats by the number of different species seen there."""
    return controllers.list_top_habitats(limit)


@router.get(
    "/stats/never-sighted-species",
    response_model=list[Species],
    tags=["Stats"],
    summary="Species nobody has ever spotted",
)
def never_sighted_species(limit: Limit = 20, offset: Offset = 0):
    """List species that have no sightings."""
    return controllers.list_never_sighted_species(limit, offset)


@router.get(
    "/stats/top-observers",
    response_model=list[TopObserver],
    tags=["Stats"],
    summary="Most active observers",
)
def top_observers(
    limit: TopN = 10,
    min_sightings: Annotated[int, Query(ge=1, description="Only include observers with at least this many sightings.")] = 850,
):
    """Rank observers by their sightings, filtering out those below min_sightings."""
    return controllers.list_top_observers(limit, min_sightings)


@router.get(
    "/stats/endangered-by-ocean",
    response_model=list[OceanThreatSummary],
    tags=["Stats"],
    summary="Endangered sightings per ocean (recent)",
)
def endangered_by_ocean(
    days: Annotated[int, Query(ge=1, le=730, description="Look back this many days from today.")] = 180,
):
    """Count recent sightings of endangered and critically endangered species by ocean."""
    return controllers.list_endangered_by_ocean(days)


@router.get(
    "/stats/species-summary",
    response_model=SpeciesSummary,
    tags=["Stats"],
    summary="Species counts by category and status",
)
def species_summary():
    """Count species by category and conservation status for dashboard summaries."""
    return controllers.species_summary()
