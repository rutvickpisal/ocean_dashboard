"""Application workflows between API controllers and repositories."""

from typing import Any

from ..repositories import repository as repositories

Row = dict[str, Any]


def check_database() -> bool:
    return repositories.check_database() is not None


def list_species(limit: int, offset: int, category: str | None, conservation_status: str | None) -> list[Row]:
    return repositories.list_species(limit, offset, category, conservation_status)


def get_species(species_id: int) -> Row | None:
    return repositories.get_species(species_id)


def list_species_habitats(species_id: int, limit: int, offset: int) -> list[Row] | None:
    if not repositories.species_exists(species_id):
        return None
    return repositories.list_species_habitats(species_id, limit, offset)


def list_habitats(limit: int, offset: int, ocean: str | None, depth_zone: str | None) -> list[Row]:
    return repositories.list_habitats(limit, offset, ocean, depth_zone)


def get_habitat(habitat_id: int) -> Row | None:
    return repositories.get_habitat(habitat_id)


def list_habitat_species(habitat_id: int, limit: int, offset: int) -> list[Row] | None:
    if not repositories.habitat_exists(habitat_id):
        return None
    return repositories.list_habitat_species(habitat_id, limit, offset)


def list_observers(limit: int, offset: int, country: str | None) -> list[Row]:
    return repositories.list_observers(limit, offset, country)


def list_sightings(
    limit: int,
    offset: int,
    species_id: int | None,
    habitat_id: int | None,
    observer_id: int | None,
) -> list[Row]:
    return repositories.list_sightings(limit, offset, species_id, habitat_id, observer_id)


def list_top_habitats(limit: int) -> list[Row]:
    return repositories.list_top_habitats(limit)


def list_never_sighted_species(limit: int, offset: int) -> list[Row]:
    return repositories.list_never_sighted_species(limit, offset)


def list_top_observers(limit: int, min_sightings: int) -> list[Row]:
    return repositories.list_top_observers(limit, min_sightings)


def list_endangered_by_ocean(days: int) -> list[Row]:
    return repositories.list_endangered_by_ocean(days)


def species_summary() -> dict[str, Any]:
    by_category = repositories.species_counts_by_category()
    by_status = repositories.species_counts_by_status()
    return {
        "total": sum(row["count"] for row in by_category),
        "by_category": by_category,
        "by_status": by_status,
    }
