"""HTTP-facing controller behavior for routes."""

from typing import Any

from fastapi import HTTPException

from ..services import service as services

Row = dict[str, Any]


def health() -> dict[str, str]:
    try:
        services.check_database()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is not reachable") from exc
    return {"status": "ok", "database": "connected"}


def list_species(limit: int, offset: int, category: str | None, conservation_status: str | None) -> list[Row]:
    return services.list_species(limit, offset, category, conservation_status)


def get_species(species_id: int) -> Row:
    row = services.get_species(species_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Species not found")
    return row


def list_species_habitats(species_id: int, limit: int, offset: int) -> list[Row]:
    rows = services.list_species_habitats(species_id, limit, offset)
    if rows is None:
        raise HTTPException(status_code=404, detail="Species not found")
    return rows


def list_habitats(limit: int, offset: int, ocean: str | None, depth_zone: str | None) -> list[Row]:
    return services.list_habitats(limit, offset, ocean, depth_zone)


def get_habitat(habitat_id: int) -> Row:
    row = services.get_habitat(habitat_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Habitat not found")
    return row


def list_habitat_species(habitat_id: int, limit: int, offset: int) -> list[Row]:
    rows = services.list_habitat_species(habitat_id, limit, offset)
    if rows is None:
        raise HTTPException(status_code=404, detail="Habitat not found")
    return rows


def list_observers(limit: int, offset: int, country: str | None) -> list[Row]:
    return services.list_observers(limit, offset, country)


def list_sightings(
    limit: int,
    offset: int,
    species_id: int | None,
    habitat_id: int | None,
    observer_id: int | None,
) -> list[Row]:
    return services.list_sightings(limit, offset, species_id, habitat_id, observer_id)


def list_top_habitats(limit: int) -> list[Row]:
    return services.list_top_habitats(limit)


def list_never_sighted_species(limit: int, offset: int) -> list[Row]:
    return services.list_never_sighted_species(limit, offset)


def list_top_observers(limit: int, min_sightings: int) -> list[Row]:
    return services.list_top_observers(limit, min_sightings)


def list_endangered_by_ocean(days: int) -> list[Row]:
    return services.list_endangered_by_ocean(days)


def species_summary() -> dict[str, Any]:
    return services.species_summary()
